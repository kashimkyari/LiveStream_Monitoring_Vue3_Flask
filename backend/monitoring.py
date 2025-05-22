import os
import time
import logging
import numpy as np
from datetime import datetime, timedelta
import av
import json
import hashlib
import requests
from flask import current_app
from models import (
    ChatKeyword, FlaggedObject, DetectionLog, Stream, User, Assignment,
    ChaturbateStream, StripchatStream
)
from extensions import db
from utils.notifications import emit_notification, emit_stream_update
from sqlalchemy.orm import joinedload
import gevent
from gevent.pool import Pool
from gevent.lock import Semaphore
from audio_processing import process_audio_segment, log_audio_detection
from video_processing import process_video_frame, log_video_detection
from chat_processing import fetch_chat_messages, process_chat_messages, log_chat_detection, initialize_chat_globals, load_sentiment_analyzer, fetch_chaturbate_room_uid
from dotenv import load_dotenv
from time import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global variables
_whisper_model = None
_whisper_lock = Semaphore()
_yolo_model = None
_yolo_lock = Semaphore()
_sentiment_analyzer = None
last_visual_alerts = {}
last_chat_alerts = {}
stream_processors = {}
agent_cache = {}
all_agents_fetched = False
gevent_pool = Pool(1)  # Limit to one worker to prevent duplicates

# Directory for transcriptions
TRANSCRIPTION_DIR = os.getenv('TRANSCRIPTION_DIR', '/home/ec2-user/LiveStream_Monitoring_Vue3_Flask/backend/transcriptions/')

# Initialize monitoring globals
def initialize_monitoring():
    """Initialize global variables for monitoring"""
    logger.info("Initializing monitoring globals")
    global _whisper_model, _whisper_lock, _sentiment_analyzer
    from audio_processing import initialize_audio_globals
    initialize_audio_globals(
        whisper_model=_whisper_model,
        whisper_lock=_whisper_lock
    )
    initialize_chat_globals(
        sentiment_analyzer=_sentiment_analyzer,
        enable_chat_monitoring=os.getenv('ENABLE_CHAT_MONITORING', 'false').lower() == 'true',
        chat_alert_cooldown=int(os.getenv('CHAT_ALERT_COOLDOWN', 60)),
        negative_sentiment_threshold=float(os.getenv('NEGATIVE_SENTIMENT_THRESHOLD', -0.5))
    )

# Model loading
def load_whisper_model():
    """Load the OpenAI Whisper model with configurable size and fallback"""
    enable_audio_monitoring = os.getenv('ENABLE_AUDIO_MONITORING', 'false').lower() == 'true'
    if not enable_audio_monitoring:
        logger.info("Audio monitoring disabled; skipping Whisper model loading")
        return None
    global _whisper_model
    with _whisper_lock:
        if _whisper_model is None:
            try:
                import whisper
                model_size = os.getenv('WHISPER_MODEL_SIZE', 'base')
                logger.info(f"Loading Whisper model: {model_size}")
                _whisper_model = whisper.load_model(model_size)
                logger.info(f"Whisper model '{model_size}' loaded successfully")
            except AttributeError as e:
                logger.error(f"Whisper attribute error: {e}. Ensure 'openai-whisper' is installed correctly.")
                try:
                    logger.info("Attempting to load fallback 'base' model")
                    _whisper_model = whisper.load_model("base")
                    logger.info("Fallback Whisper model loaded")
                except Exception as e2:
                    logger.error(f"Error loading fallback model: {e2}")
                    _whisper_model = None
            except Exception as e:
                logger.error(f"Error loading Whisper model: {e}")
                _whisper_model = None
    if _whisper_model is None:
        logger.warning("Whisper model unavailable; audio processing will be skipped.")
    return _whisper_model

def load_yolo_model():
    """Load the YOLO object detection model"""
    enable_video_monitoring = os.getenv('ENABLE_VIDEO_MONITORING', 'false').lower() == 'true'
    if not enable_video_monitoring:
        logger.info("Video monitoring disabled; skipping YOLO model loading")
        return None
    global _yolo_model
    with _yolo_lock:
        if _yolo_model is None:
            try:
                from ultralytics import YOLO
                import torch
                torch.backends.nnpack.enabled = False  # Disable NNPACK to avoid warnings
                _yolo_model = YOLO("yolov8s.pt", verbose=False)
                _yolo_model.verbose = False
                logger.info("YOLO model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading YOLO model: {e}")
                _yolo_model = None
    return _yolo_model

def load_sentiment_analyzer():
    """Load the VADER sentiment analyzer"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        _sentiment_analyzer = SentimentIntensityAnalyzer()
    return _sentiment_analyzer

# Data retrieval functions
def refresh_flagged_keywords():
    """Retrieve current flagged keywords from database"""
    with current_app.app_context():
        keywords = [kw.keyword.lower() for kw in ChatKeyword.query.all()]
    logger.debug(f"Retrieved {len(keywords)} flagged keywords")
    return keywords

def refresh_flagged_objects():
    """Retrieve flagged objects and confidence thresholds"""
    with current_app.app_context():
        objects = FlaggedObject.query.all()
        flagged = {obj.object_name.lower(): float(obj.confidence_threshold) for obj in objects}
    logger.debug(f"Retrieved {len(flagged)} flagged objects")
    return flagged

def get_stream_info(stream_url):
    """Identify platform and streamer from URL"""
    with current_app.app_context():
        cb_stream = ChaturbateStream.query.filter_by(chaturbate_m3u8_url=stream_url).first()
        if cb_stream:
            return 'chaturbate', cb_stream.streamer_username
        sc_stream = StripchatStream.query.filter_by(stripchat_m3u8_url=stream_url).first()
        if sc_stream:
            return 'stripchat', sc_stream.streamer_username
        stream = Stream.query.filter_by(room_url=stream_url).first()
        if stream:
            return stream.type.lower(), stream.streamer_username
    return 'unknown', 'unknown'

def get_m3u8_url(stream):
    """Get the m3u8 URL for a stream"""
    with current_app.app_context():
        if stream.type.lower() == 'chaturbate':
            cb_stream = ChaturbateStream.query.get(stream.id)
            return cb_stream.chaturbate_m3u8_url if cb_stream else None
        elif stream.type.lower() == 'stripchat':
            sc_stream = StripchatStream.query.get(stream.id)
            return sc_stream.stripchat_m3u8_url if sc_stream else None
    return None

def fetch_all_agents():
    """Fetch all agents and cache their usernames"""
    global all_agents_fetched
    with current_app.app_context():
        if all_agents_fetched:
            return
        try:
            agents = User.query.filter_by(role='agent').all()
            for agent in agents:
                agent_cache[agent.id] = agent.username or f"Agent {agent.id}"
            all_agents_fetched = True
            logger.info(f"Cached {len(agent_cache)} agent usernames")
        except Exception as e:
            logger.error(f"Error fetching all agents: {e}")

def fetch_agent_username(agent_id):
    """Fetch a single agent's username and cache it"""
    with current_app.app_context():
        if agent_id in agent_cache:
            return agent_cache[agent_id]
        try:
            agent = User.query.get(agent_id)
            if agent:
                agent_cache[agent_id] = agent.username or f"Agent {agent_id}"
                return agent_cache[agent_id]
            else:
                logger.warning(f"Agent {agent_id} not found")
                agent_cache[agent_id] = f"Agent {agent_id}"
                return agent_cache[agent_id]
        except Exception as e:
            logger.error(f"Error fetching username for agent {agent_id}: {e}")
            agent_cache[agent_id] = f"Agent {agent_id}"
            return agent_cache[agent_id]

def get_stream_assignment(stream_url):
    """Get assignment info for a stream"""
    with current_app.app_context():
        stream = Stream.query.filter_by(room_url=stream_url).first()
        if not stream:
            cb_stream = ChaturbateStream.query.filter_by(chaturbate_m3u8_url=stream_url).first()
            if cb_stream:
                stream = Stream.query.get(cb_stream.id)
            else:
                sc_stream = StripchatStream.query.filter_by(stripchat_m3u8_url=stream_url).first()
                if sc_stream:
                    stream = Stream.query.get(sc_stream.id)
        if not stream:
            logger.warning(f"No stream found for URL: {stream_url}")
            return None, None
        query = Assignment.query.options(
            joinedload(Assignment.agent),
            joinedload(Assignment.stream)
        ).filter_by(stream_id=stream.id)
        assignments = query.all()
        if not assignments:
            logger.info(f"No assignments found for stream: {stream_url}")
            return None, None
        assignment = assignments[0]
        agent_id = assignment.agent_id
        fetch_agent_username(agent_id)
        return assignment.id, agent_id

def save_transcription_to_json(stream_url, transcript, detected_keywords):
    """Save transcription to a JSON file with metadata"""
    try:
        os.makedirs(TRANSCRIPTION_DIR, exist_ok=True)
        url_hash = hashlib.md5(stream_url.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcription_{url_hash}_{timestamp}.json"
        filepath = os.path.join(TRANSCRIPTION_DIR, filename)
        data = {
            "stream_url": stream_url,
            "timestamp": datetime.now().isoformat(),
            "transcription": transcript,
            "detected_keywords": detected_keywords
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved transcription to {filepath}")
    except Exception as e:
        logger.error(f"Error saving transcription to JSON for {stream_url}: {e}")

def check_stream_availability(stream_url, timeout=10):
    """Check if the stream URL is accessible"""
    try:
        response = requests.head(stream_url, timeout=timeout)
        if response.status_code == 200:
            logger.debug(f"Stream URL {stream_url} is accessible")
            return True
        else:
            logger.warning(f"Stream URL {stream_url} returned status code {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"Error checking stream availability for {stream_url}: {e}")
        return False

def process_combined_detection(app, stream_url, cancel_event):
    """Main monitoring loop processing audio, video, and chat from M3U8 stream with separate AV containers"""
    with app.app_context():
        logger.info(f"Starting monitoring for {stream_url}")
        # Query stream info to get the stream ID
        stream = Stream.query.filter_by(room_url=stream_url).first()
        if not stream:
            cb_stream = ChaturbateStream.query.filter_by(chaturbate_m3u8_url=stream_url).first()
            if cb_stream:
                stream = Stream.query.get(cb_stream.id)
            else:
                sc_stream = StripchatStream.query.filter_by(stripchat_m3u8_url=stream_url).first()
                if sc_stream:
                    stream = Stream.query.get(sc_stream.id)
        if not stream:
            logger.error(f"Stream not found for URL: {stream_url}")
            return
        stream_id = stream.id  # Store stream ID for re-querying

        enable_video_monitoring = os.getenv('ENABLE_VIDEO_MONITORING', 'true').lower() == 'true'
        enable_audio_monitoring = os.getenv('ENABLE_AUDIO_MONITORING', 'true').lower() == 'true'
        enable_chat_monitoring = os.getenv('ENABLE_CHAT_MONITORING', 'true').lower() == 'true'

        if not (enable_video_monitoring or enable_audio_monitoring or enable_chat_monitoring):
            logger.error(f"No monitoring types enabled for {stream_url}")
            return

        last_chat_process_time = None
        keywords = refresh_flagged_keywords()
        max_retries = 3
        retry_delay = 10  # Seconds between retries
        frame_process_times = {}  # Dictionary to store last process time per stream

        while not cancel_event.is_set():
            with app.app_context():
                # Re-query the stream to ensure it's in the current session
                stream = Stream.query.get(stream_id)
                if not stream:
                    logger.error(f"Stream with ID {stream_id} no longer exists")
                    break
                try:
                    db.session.refresh(stream)
                    if stream.status == 'offline':
                        logger.info(f"Stopping monitoring for offline stream: {stream.id}")
                        stop_monitoring(stream)
                        break
                except Exception as e:
                    logger.error(f"Error refreshing stream {stream_id}: {e}")
                    break

            if enable_video_monitoring:
                retry_count = 0
                stream_available = False
                while retry_count < max_retries and not cancel_event.is_set():
                    if check_stream_availability(stream_url):
                        stream_available = True
                        break
                    logger.warning(f"Stream {stream_url} unavailable, retrying ({retry_count + 1}/{max_retries})")
                    retry_count += 1
                    gevent.sleep(retry_delay)

                if not stream_available:
                    logger.error(f"Stream {stream_url} is offline or inaccessible after {max_retries} retries")
                    with app.app_context():
                        stream = Stream.query.get(stream_id)
                        if stream:
                            stream.status = 'offline'
                            db.session.commit()
                            stop_monitoring(stream)
                    break

                try:
                    video_container = av.open(stream_url, timeout=60)
                    logger.info(f"Video stream opened successfully: {stream_url}")
                    video_stream = next((s for s in video_container.streams if s.type == 'video'), None)
                    if video_stream:
                        for packet in video_container.demux(video_stream):
                            if cancel_event.is_set():
                                break
                            try:
                                for frame in packet.decode():
                                    frame_time = frame.pts * float(video_stream.time_base)
                                    last_process_time = frame_process_times.get(stream_url)
                                    if last_process_time is None or frame_time - last_process_time >= 5:
                                        img = frame.to_ndarray(format='bgr24')
                                        detections = process_video_frame(img, stream_url)
                                        if detections:
                                            log_video_detection(detections, img, stream_url)
                                        frame_process_times[stream_url] = frame_time
                                        logger.debug(f"Processed frame for {stream_url} at time {frame_time}")
                            except av.error.InvalidDataError as e:
                                logger.warning(f"Invalid data error while decoding video packet for {stream_url}: {e}")
                                continue
                            except Exception as e:
                                logger.error(f"Unexpected error decoding video packet for {stream_url}: {e}")
                                continue
                    video_container.close()
                except av.error.EOFError as e:
                    logger.error(f"EOF error opening video stream {stream_url}: {e}")
                    with app.app_context():
                        stream = Stream.query.get(stream_id)
                        if stream:
                            stream.status = 'offline'
                            db.session.commit()
                            stop_monitoring(stream)
                    break
                except av.error.OSError as e:
                    logger.error(f"OS error opening video stream {stream_url}: {e}")
                    gevent.sleep(retry_delay)
                    continue
                except av.error.ValueError as e:
                    logger.error(f"Value error opening video stream {stream_url}: {e}")
                    gevent.sleep(retry_delay)
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error opening video stream {stream_url}: {e}")
                    gevent.sleep(retry_delay)
                    continue

            if enable_audio_monitoring:
                try:
                    audio_container = av.open(stream_url, timeout=60)
                    logger.info(f"Audio stream opened successfully: {stream_url}")
                    audio_stream = next((s for s in audio_container.streams if s.type == 'audio'), None)
                    if audio_stream:
                        audio_buffer = []
                        total_audio_duration = 0
                        sample_rate = audio_stream.rate if audio_stream else 16000
                        for packet in audio_container.demux(audio_stream):
                            if cancel_event.is_set():
                                break
                            try:
                                for frame in packet.decode():
                                    audio_data = frame.to_ndarray().flatten().astype(np.float32) / 32768.0
                                    frame_duration = frame.samples / sample_rate
                                    audio_buffer.append(audio_data)
                                    total_audio_duration += frame_duration
                                    if total_audio_duration >= current_app.config['AUDIO_SAMPLE_DURATION']:
                                        combined_audio = np.concatenate(audio_buffer)
                                        detections, transcript = process_audio_segment(combined_audio, sample_rate, stream_url)
                                        logger.info(f"Transcription for {stream_url} at {datetime.now().isoformat()}:\n{transcript}")
                                        detected_keywords = []
                                        if keywords and transcript:
                                            detected_keywords = [kw for kw in keywords if kw in transcript.lower()]
                                            if detected_keywords:
                                                logger.info(f"Keywords detected in transcription: {detected_keywords}")
                                        save_transcription_to_json(stream_url, transcript, detected_keywords)
                                        for detection in detections:
                                            log_audio_detection(detection, stream_url)
                                            platform, streamer = get_stream_info(stream_url)
                                            notification_data = {
                                                "event_type": "audio_keyword_alert",
                                                "timestamp": detection["timestamp"],
                                                "details": {
                                                    "keyword": detection["keyword"],
                                                    "transcript": detection["transcript"],
                                                    "streamer_name": streamer,
                                                    "platform": platform,
                                                    "stream_url": stream_url
                                                },
                                                "read": False,
                                                "room_url": stream_url,
                                                "streamer": streamer,
                                                "platform": platform,
                                                "assigned_agent": "Unassigned"
                                            }
                                            emit_notification(notification_data)
                                        if detected_keywords:
                                            platform, streamer = get_stream_info(stream_url)
                                            notification_data = {
                                                "event_type": "audio_keyword_alert",
                                                "timestamp": datetime.now().isoformat(),
                                                "details": {
                                                    "keyword": detected_keywords,
                                                    "transcript": transcript,
                                                    "streamer_name": streamer or "unknown",
                                                    "platform": platform or "unknown",
                                                    "stream_url": stream_url
                                                },
                                                "read": False,
                                                "room_url": stream_url,
                                                "streamer": streamer or "unknown",
                                                "platform": platform or "unknown",
                                                "assigned_agent": "Unassigned"
                                            }
                                            emit_notification(notification_data)
                                        audio_buffer = []
                                        total_audio_duration = 0
                            except Exception as e:
                                logger.error(f"Error processing audio frame for {stream_url}: {e}")
                                continue
                    audio_container.close()
                except av.error.OSError as e:
                    logger.error(f"OS error opening audio stream {stream_url}: {e}", exc_info=True)
                    gevent.sleep(10)
                except av.error.ValueError as e:
                    logger.error(f"Value error opening audio stream {stream_url}: {e}", exc_info=True)
                    gevent.sleep(10)
                except Exception as e:
                    logger.error(f"Unexpected error opening audio stream {stream_url}: {e}", exc_info=True)
                    gevent.sleep(10)

            if enable_chat_monitoring:
                current_time = time.time()
                if last_chat_process_time is None or current_time - last_chat_process_time >= 30:
                    messages = fetch_chat_messages(stream.room_url)
                    chat_detections = process_chat_messages(messages, stream.room_url)
                    log_chat_detection(chat_detections, stream.room_url)
                    last_chat_process_time = current_time
            
            if not (enable_video_monitoring or enable_audio_monitoring):
                gevent.sleep(10)

        logger.info(f"Stopped monitoring {stream_url}")

def start_monitoring(stream):
    """Start monitoring a stream for detections, fetching and saving broadcaster_uid for Chaturbate streams if needed"""
    start_time = time()
    current_app.logger.info(f"Starting monitoring for stream {stream.id}")
    if not stream:
        logger.error("Stream not provided")
        return False
    continuous_monitoring = os.getenv('CONTINUOUS_MONITORING', 'true').lower() == 'true'
    if not continuous_monitoring:
        logger.info(f"Continuous monitoring disabled; skipping stream {stream.room_url}")
        return False
    if stream.status == 'offline':
        logger.info(f"Cannot start monitoring for offline stream: {stream.id}")
        return False

    with current_app.app_context():
        if stream.is_monitored:
            logger.info(f"Stream already monitored: {stream.room_url}")
            return True
        
        if stream.type.lower() == 'chaturbate':
            cb_stream = ChaturbateStream.query.get(stream.id)
            if cb_stream and not cb_stream.broadcaster_uid:
                logger.info(f"Fetching broadcaster_uid for Chaturbate stream: {stream.streamer_username}")
                broadcaster_uid, _ = fetch_chaturbate_room_uid(stream.streamer_username)
                if broadcaster_uid:
                    cb_stream.broadcaster_uid = broadcaster_uid
                    try:
                        db.session.commit()
                        logger.info(f"Saved broadcaster_uid {broadcaster_uid} for stream {stream.room_url}")
                    except Exception as e:
                        logger.error(f"Failed to save broadcaster_uid for {stream.room_url}: {e}")
                        db.session.rollback()
                else:
                    logger.warning(f"Could not fetch broadcaster_uid for {stream.streamer_username}; proceeding without it")
        
        stream.is_monitored = True
        db.session.commit()
    
    stream_url = get_m3u8_url(stream)
    if not stream_url:
        logger.error(f"No valid m3u8 URL for stream: {stream.id}")
        return False
    
    # Check if stream is already being monitored
    if stream_url in stream_processors:
        logger.info(f"Stream {stream_url} is already being monitored by another worker")
        return True
    
    logger.info(f"Starting monitoring for {stream_url}")
    cancel_event = gevent.event.Event()
    task = gevent_pool.spawn(
        process_combined_detection,
        current_app._get_current_object(),
        stream_url,
        cancel_event
    )
    stream_processors[stream_url] = (cancel_event, task)
    emit_stream_update({
        'id': stream.id,
        'url': stream_url,
        'status': 'monitoring',
        'type': stream.type,
        'isDetecting': True
    })
    current_app.logger.info(f"start_monitoring took {time() - start_time:.2f} seconds")
    return True

def stop_monitoring(stream):
    """Stop monitoring a stream"""
    start_time = time()
    current_app.logger.info(f"Stopping monitoring for stream {stream.id}")
    if not stream:
        logger.error("Stream not provided")
        return
    
    stream_url = get_m3u8_url(stream)
    if not stream_url:
        stream_url = stream.room_url
    
    with current_app.app_context():
        stream.is_monitored = False
        db.session.commit()
    
    if stream_url in stream_processors:
        cancel_event, task = stream_processors.get(stream_url, (None, None))
        if cancel_event:
            cancel_event.set()
            if task:
                task.join(timeout=2.0)
        del stream_processors[stream_url]
    
    logger.info(f"Stopped monitoring {stream_url}")
    emit_stream_update({
        'id': stream.id,
        'url': stream_url,
        'status': 'stopped',
        'type': stream.type,
        'isDetecting': False
    })
    current_app.logger.info(f"stop_monitoring took {time() - start_time:.2f} seconds")

def refresh_and_monitor_streams(stream_ids):
    """Refresh and monitor selected streams"""
    continuous_monitoring = os.getenv('CONTINUOUS_MONITORING', 'true').lower() == 'true'
    if not continuous_monitoring:
        logger.info("Continuous monitoring disabled; skipping stream refresh")
        return False
    with current_app.app_context():
        streams = Stream.query.filter(Stream.id.in_(stream_ids)).all()
        if not streams:
            logger.warning("No streams found for provided IDs")
            return False
        tasks = []
        for stream in streams:
            try:
                if stream.is_monitored:
                    stop_monitoring(stream)
                if stream.type.lower() == 'chaturbate':
                    endpoint = '/api/streams/refresh/chaturbate'
                    payload = {'room_slug': stream.streamer_username}
                elif stream.type.lower() == 'stripchat':
                    endpoint = '/api/streams/refresh/stripchat'
                    payload = {'room_url': stream.room_url}
                else:
                    logger.warning(f"Unsupported platform {stream.type} for stream {stream.id}")
                    continue
                logger.info(f"Refreshing stream {stream.id} ({stream.type})")
                task = gevent_pool.spawn(
                    lambda: requests.post(
                        f"{current_app.config['BASE_URL']}{endpoint}",
                        json=payload,
                        timeout=10
                    )
                )
                tasks.append((stream, task))
            except Exception as e:
                logger.error(f"Error initiating stream refresh {stream.id}: {e}")
                continue
        for stream, task in tasks:
            try:
                response = task.get()
                if response.status_code == 200 and response.json().get('m3u8_url'):
                    db.session.refresh(stream)
                    start_monitoring(stream)
                    logger.info(f"Successfully refreshed and started monitoring stream {stream.id}")
                else:
                    logger.error(f"Failed to refresh stream {stream.id}: {response.text}")
            except Exception as e:
                logger.error(f"Error processing stream {stream.id}: {e}")
                continue
        return True

def start_notification_monitor():
    """Initialize background tasks for notifications monitoring"""
    continuous_monitoring = os.getenv('CONTINUOUS_MONITORING', 'true').lower() == 'true'
    if not continuous_monitoring:
        logger.info("Continuous monitoring disabled; notification monitor not started")
        return
    logger.info("Starting notification monitor")
    try:
        with current_app.app_context():
            streams = Stream.query.filter(Stream.status != 'offline').all()
            logger.info(f"Found {len(streams)} streams to monitor")
            for stream in streams:
                logger.info(f"Attempting to start monitoring for stream {stream.id} ({stream.room_url})")
                try:
                    if start_monitoring(stream):
                        logger.info(f"Successfully started monitoring for stream {stream.id}")
                    else:
                        logger.warning(f"Failed to start monitoring for stream {stream.id}")
                except Exception as e:
                    logger.error(f"Error starting monitoring for stream {stream.id}: {str(e)}")
            logger.info("Notification monitor started successfully")
    except Exception as e:
        logger.error(f"Error starting notification monitor: {str(e)}")
        raise

# Exports
__all__ = [
    'start_monitoring',
    'stop_monitoring',
    'process_audio_segment',
    'process_video_frame',
    'process_chat_messages',
    'start_notification_monitor',
    'refresh_and_monitor_streams',
    'initialize_monitoring'
]