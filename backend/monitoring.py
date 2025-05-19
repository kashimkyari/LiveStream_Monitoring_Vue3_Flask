import os
import time
import logging
import numpy as np
from datetime import datetime, timedelta
import av
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
from chat_processing import fetch_chat_messages, process_chat_messages, log_chat_detection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# =============== ENVIRONMENT VARIABLE CONFIGURATION ===============
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")
AUDIO_SAMPLE_DURATION = int(os.environ.get("AUDIO_SAMPLE_DURATION", "10"))
VISUAL_ALERT_COOLDOWN = int(os.environ.get("VISUAL_ALERT_COOLDOWN", "30"))
CHAT_ALERT_COOLDOWN = int(os.environ.get("CHAT_ALERT_COOLDOWN", "45"))
NEGATIVE_SENTIMENT_THRESHOLD = float(os.environ.get("NEGATIVE_SENTIMENT_THRESHOLD", "-0.5"))
CONTINUOUS_MONITORING = os.environ.get("CONTINUOUS_MONITORING", "true").lower() == "true"
ENABLE_AUDIO_MONITORING = os.environ.get("ENABLE_AUDIO_MONITORING", "true").lower() == "true"
ENABLE_VIDEO_MONITORING = os.environ.get("ENABLE_VIDEO_MONITORING", "true").lower() == "true"
ENABLE_CHAT_MONITORING = os.environ.get("ENABLE_CHAT_MONITORING", "true").lower() == "true"

# =============== GLOBAL VARIABLES ===============
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
gevent_pool = Pool(5)

# =============== MODEL LOADING ===============
def load_whisper_model():
    """Load the OpenAI Whisper model with configurable size and fallback"""
    if not ENABLE_AUDIO_MONITORING:
        logger.info("Audio monitoring disabled; skipping Whisper model loading")
        return None
    global _whisper_model
    with _whisper_lock:
        if _whisper_model is None:
            try:
                import whisper
                logger.info(f"Loading Whisper model: {WHISPER_MODEL_SIZE}")
                _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
                logger.info(f"Whisper model '{WHISPER_MODEL_SIZE}' loaded successfully")
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
    if not ENABLE_VIDEO_MONITORING:
        logger.info("Video monitoring disabled; skipping YOLO model loading")
        return None
    global _yolo_model
    with _yolo_lock:
        if _yolo_model is None:
            try:
                from ultralytics import YOLO
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

# =============== DATA RETRIEVAL FUNCTIONS ===============
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

# =============== MAIN PROCESSING LOOP ===============
def process_combined_detection(app, stream_url, cancel_event):
    """Main monitoring loop processing audio, video, and chat from M3U8 stream"""
    with app.app_context():
        logger.info(f"Starting monitoring for {stream_url}")
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

        while not cancel_event.is_set():
            if stream.status == 'offline':
                logger.info(f"Stopping monitoring for offline stream: {stream.id}")
                stop_monitoring(stream)
                break

            try:
                container = av.open(stream_url, timeout=30)
                video_stream = next((s for s in container.streams if s.type == 'video'), None) if ENABLE_VIDEO_MONITORING else None
                audio_stream = next((s for s in container.streams if s.type == 'audio'), None) if ENABLE_AUDIO_MONITORING else None
                
                if not (video_stream or audio_stream or ENABLE_CHAT_MONITORING):
                    logger.error(f"No enabled monitoring types for {stream_url}")
                    gevent.sleep(10)
                    continue

                audio_buffer = []
                total_audio_duration = 0
                sample_rate = audio_stream.rate if audio_stream else 16000
                last_process_time = None
                last_chat_process_time = None

                for packet in container.demux():
                    if cancel_event.is_set():
                        break
                    if ENABLE_VIDEO_MONITORING and packet.stream == video_stream:
                        for frame in packet.decode():
                            frame_time = frame.pts * float(video_stream.time_base)
                            if last_process_time is None or frame_time - last_process_time >= 5:
                                img = frame.to_ndarray(format='bgr24')
                                detections = process_video_frame(img, stream_url)
                                if detections:
                                    log_video_detection(detections, img, stream_url)
                                last_process_time = frame_time
                    elif ENABLE_AUDIO_MONITORING and packet.stream == audio_stream:
                        for frame in packet.decode():
                            audio_data = frame.to_ndarray().flatten().astype(np.float32) / 32768.0
                            frame_duration = frame.samples / sample_rate
                            audio_buffer.append(audio_data)
                            total_audio_duration += frame_duration
                            if total_audio_duration >= AUDIO_SAMPLE_DURATION:
                                combined_audio = np.concatenate(audio_buffer)
                                detections = process_audio_segment(combined_audio, sample_rate, stream_url)
                                for detection in detections:
                                    log_audio_detection(detection, stream_url)
                                audio_buffer = []
                                total_audio_duration = 0
                    if ENABLE_CHAT_MONITORING:
                        current_time = time.time()
                        if last_chat_process_time is None or current_time - last_chat_process_time >= 30:
                            messages = fetch_chat_messages(stream.room_url)
                            chat_detections = process_chat_messages(messages, stream.room_url)
                            log_chat_detection(chat_detections, stream.room_url)
                            last_chat_process_time = current_time
            except Exception as e:
                logger.error(f"Stream error: {e}")
                gevent.sleep(10)
        logger.info(f"Stopped monitoring {stream_url}")

# =============== MAIN MONITORING CONTROL ===============
def start_monitoring(stream):
    """Start monitoring a stream for detections"""
    if not stream:
        logger.error("Stream not provided")
        return False
    if not CONTINUOUS_MONITORING:
        logger.info(f"Continuous monitoring disabled; skipping stream {stream.room_url}")
        return False
    if stream.status == 'offline':
        logger.info(f"Cannot start monitoring for offline stream: {stream.id}")
        return False

    with current_app.app_context():
        if stream.is_monitored:
            logger.info(f"Stream already monitored: {stream.room_url}")
            return True
        stream.is_monitored = True
        db.session.commit()
    
    stream_url = get_m3u8_url(stream)
    if not stream_url:
        logger.error(f"No valid m3u8 URL for stream: {stream.id}")
        return False
    
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
        'type': stream.type
    })
    return True

def stop_monitoring(stream):
    """Stop monitoring a stream"""
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
        'type': stream.type
    })

def refresh_and_monitor_streams(stream_ids):
    """Refresh and monitor selected streams"""
    if not CONTINUOUS_MONITORING:
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
    if not CONTINUOUS_MONITORING:
        logger.info("Continuous monitoring disabled; notification monitor not started")
        return
    logger.info("Starting notification monitor")
    try:
        with current_app.app_context():
            streams = Stream.query.filter_by(is_monitored=True).all()
            for stream in streams:
                if stream.status != 'offline':
                    start_monitoring(stream)
                else:
                    logger.info(f"Skipping offline stream {stream.id} during notification monitor startup")
        logger.info("Notification monitor started successfully")
    except Exception as e:
        logger.error(f"Error starting notification monitor: {e}")
        raise

# =============== EXPORTS ===============
__all__ = [
    'start_monitoring',
    'stop_monitoring',
    'process_audio_segment',
    'process_video_frame',
    'process_chat_messages',
    'start_notification_monitor',
    'refresh_and_monitor_streams'
]

if __name__ == "__main__":
    print("Livestream monitoring system - import this module to use")