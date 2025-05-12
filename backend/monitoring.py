# monitoring.py - Complete Upgraded Version
import os
import time
import threading
import logging
import numpy as np
import json
import base64
import cv2
import requests
from datetime import datetime, timedelta
import io
from PIL import Image
import whisper
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import torch
import av
import re
import tempfile
import subprocess
import queue
import ffmpeg
from bs4 import BeautifulSoup
import pytesseract
from urllib.parse import urlparse
from scipy import signal
from io import BytesIO

from flask import current_app
from models import (
    ChatKeyword, FlaggedObject, DetectionLog, Stream, User, Assignment,
    ChaturbateStream, StripchatStream, TelegramRecipient, Log
)
from extensions import db
from utils.notifications import emit_notification, emit_stream_update
from notifications import send_notifications, send_text_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

_app = None

# =============== ENVIRONMENT VARIABLE CONFIGURATION ===============
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")
AUDIO_SAMPLE_DURATION = int(os.environ.get("AUDIO_SAMPLE_DURATION", "10"))
AUDIO_BUFFER_SIZE = int(os.environ.get("AUDIO_BUFFER_SIZE", "3"))
AUDIO_SEGMENT_LENGTH = int(os.environ.get("AUDIO_SEGMENT_LENGTH", "5"))
AUDIO_ALERT_COOLDOWN = int(os.environ.get("AUDIO_ALERT_COOLDOWN", "60"))
VISUAL_ALERT_COOLDOWN = int(os.environ.get("VISUAL_ALERT_COOLDOWN", "30"))
CHAT_ALERT_COOLDOWN = int(os.environ.get("CHAT_ALERT_COOLDOWN", "45"))
NEGATIVE_SENTIMENT_THRESHOLD = float(os.environ.get("NEGATIVE_SENTIMENT_THRESHOLD", "-0.5"))

# =============== GLOBAL VARIABLES ===============
_whisper_model = None
_whisper_lock = threading.Lock()
_yolo_model = None
_yolo_lock = threading.Lock()
_sentiment_analyzer = SentimentIntensityAnalyzer()

# Tracking variables
last_audio_alerts = {}
last_visual_alerts = {}
last_chat_alerts = {}

# Stream processing buffers
stream_audio_buffers = {}
stream_processors = {}

# =============== MODEL LOADING ===============
def load_whisper_model():
    """Load the OpenAI Whisper model with configurable size and fallback"""
    global _whisper_model
    with _whisper_lock:
        if _whisper_model is None:
            try:
                logger.info(f"Loading Whisper model: {WHISPER_MODEL_SIZE}")
                _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
                logger.info(f"Whisper model '{WHISPER_MODEL_SIZE}' loaded successfully")
            except Exception as e:
                logger.error(f"Error loading Whisper model: {e}")
                try:
                    logger.info("Attempting to load fallback 'base' model")
                    _whisper_model = whisper.load_model("base")
                    logger.info("Fallback Whisper model loaded")
                except Exception as e2:
                    logger.error(f"Error loading fallback model: {e2}")
                    _whisper_model = None
    return _whisper_model

def load_yolo_model():
    """Load the YOLO object detection model"""
    global _yolo_model
    with _yolo_lock:
        if _yolo_model is None:
            try:
                from ultralytics import YOLO
                _yolo_model = YOLO("yolov9c.pt", verbose=False)
                _yolo_model.verbose = False
                logger.info("YOLO model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading YOLO model: {e}")
                _yolo_model = None
    return _yolo_model

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
        # Check Chaturbate first
        cb_stream = ChaturbateStream.query.filter_by(chaturbate_m3u8_url=stream_url).first()
        if cb_stream:
            return 'chaturbate', cb_stream.streamer_username
            
        # Check Stripchat next
        sc_stream = StripchatStream.query.filter_by(stripchat_m3u8_url=stream_url).first()
        if sc_stream:
            return 'stripchat', sc_stream.streamer_username
            
        # Fallback to generic stream
        stream = Stream.query.filter_by(room_url=stream_url).first()
        if stream:
            return stream.type.lower(), stream.streamer_username
            
    return 'unknown', 'unknown'

def get_stream_assignment(stream_url):
    """Get assignment info for a stream"""
    with current_app.app_context():
        stream = Stream.query.filter_by(room_url=stream_url).first()
        if not stream:
            return None, None
            
        assignment = Assignment.query.filter_by(stream_id=stream.id).first()
        if assignment:
            return assignment.id, assignment.agent_id
        
    return None, None

# =============== ENHANCED AUDIO PROCESSING ===============
def extract_audio_from_stream_ffmpeg(stream_url, output_file=None, duration=10):
    """Extract audio using FFmpeg with robust error handling"""
    try:
        if output_file is None:
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            output_file = temp_file.name
            temp_file.close()
        
        cmd = [
            'ffmpeg', '-y',
            '-i', stream_url,
            '-t', str(duration),
            '-vn',
            '-ar', '16000',
            '-ac', '1',
            '-acodec', 'pcm_s16le',
            output_file
        ]
        logger.debug(f"Executing FFmpeg command: {' '.join(cmd)}")  # Log the command
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=duration + 10
        )
        
        if process.returncode != 0:
            error_msg = process.stderr.decode('utf-8')
            logger.error(f"FFmpeg failed with return code {process.returncode}: {error_msg}")
            return None
            
        logger.debug(f"FFmpeg audio extraction successful: {output_file}")
        return output_file
    
    except subprocess.TimeoutExpired:
        logger.error(f"FFmpeg timeout processing {stream_url}")
        return None
    except Exception as e:
        logger.error(f"Audio extraction error: {e}")
        return None

def chunked_audio_processor(stream_url, cancel_event, audio_queue):
    """Background process for continuous audio chunking"""
    logger.info(f"Starting audio chunker for {stream_url}")
    
    while not cancel_event.is_set():
        try:
            audio_file = extract_audio_from_stream_ffmpeg(stream_url, duration=AUDIO_SEGMENT_LENGTH)
            
            if audio_file and os.path.exists(audio_file):
                try:
                    with open(audio_file, 'rb') as f:
                        f.seek(44)
                        audio_data = np.frombuffer(f.read(), np.int16).astype(np.float32) / 32768.0
                        
                    if audio_queue.full():
                        try:
                            audio_queue.get_nowait()
                        except queue.Empty:
                            pass
                    audio_queue.put(audio_data)
                    
                except Exception as e:
                    logger.error(f"Audio load error: {e}")
                
                try:
                    os.unlink(audio_file)
                except Exception as e:
                    logger.error(f"Temp file cleanup error: {e}")
            
            for _ in range(AUDIO_SEGMENT_LENGTH // 2):
                if cancel_event.is_set():
                    break
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Chunker error: {e}")
            time.sleep(5)
            
    logger.info(f"Stopped audio chunker for {stream_url}")

def process_audio_realtime(stream_url, cancel_event):
    """Real-time audio processing with buffering"""
    logger.info(f"Starting real-time audio for {stream_url}")
    
    if stream_url not in stream_audio_buffers:
        stream_audio_buffers[stream_url] = queue.Queue(maxsize=AUDIO_BUFFER_SIZE)
    
    audio_queue = stream_audio_buffers[stream_url]
    chunker_cancel = threading.Event()
    chunker_thread = threading.Thread(
        target=chunked_audio_processor,
        args=(stream_url, chunker_cancel, audio_queue),
        daemon=True
    )
    chunker_thread.start()
    stream_processors[stream_url] = (chunker_thread, chunker_cancel)
    
    while not cancel_event.is_set():
        try:
            audio_chunks = []
            while not audio_queue.empty() and len(audio_chunks) < AUDIO_BUFFER_SIZE:
                try:
                    chunk = audio_queue.get_nowait()
                    audio_chunks.append(chunk)
                except queue.Empty:
                    break
            
            if audio_chunks:
                audio_data = np.concatenate(audio_chunks)
                for detection in process_audio_segment(audio_data, stream_url):
                    log_audio_detection(detection, stream_url)
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            time.sleep(5)
    
    chunker_cancel.set()
    logger.info(f"Stopped real-time audio for {stream_url}")

def process_audio_segment(audio_data, stream_url):
    """Process an audio segment for transcription and analysis"""
    try:
        model = load_whisper_model()
        if model is None:
            logger.error("Whisper model not loaded")
            return None
        start_time = time.time()
        logger.info(f"Transcribing audio for {stream_url}")
        result = model.transcribe(audio_data, fp16=False)
        transcript = result.get("text", "").strip()
        logger.info(f"Transcription for {stream_url}: {transcript[:100]}...")
        logger.info(f"Transcription took {time.time() - start_time:.2f} seconds")
        if not transcript:
            logger.info(f"Empty transcription for {stream_url}")
            return None
        # Save transcript to audio_detection folder
        os.makedirs('audio_detection', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stream_id = stream_url.split('/')[-1] if '/' in stream_url else stream_url
        transcript_file = f'audio_detection/transcript_{stream_id}_{timestamp}.txt'
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript)
        logger.info(f"Transcript saved to {transcript_file}")
        # Check for keywords
        keywords = refresh_flagged_keywords()
        detected_keywords = []
        for kw in keywords:
            if kw in transcript.lower():
                detected_keywords.append(kw)
        if detected_keywords:
            sentiment = _sentiment_analyzer.polarity_scores(transcript)
            compound_score = sentiment.get("compound", 0.0)
            detection = {
                "timestamp": datetime.now().isoformat(),
                "transcript": transcript,
                "keyword": detected_keywords,
                "sentiment_score": compound_score
            }
            return [detection]  # Return as list for consistency
        return []
    except Exception as e:
        logger.error(f"Error processing audio for {stream_url}: {e}")
        return []

def log_audio_detection(detection, stream_url):
    """Log audio detections to database"""
    platform, streamer = get_stream_info(stream_url)
    assignment_id, agent_id = get_stream_assignment(stream_url)

    details = {
        "keyword": detection.get("keyword"),
        "transcript": detection.get("transcript"),
        "timestamp": detection.get("timestamp"),
        "streamer_name": streamer,
        "platform": platform,
        "assigned_agent": agent_id  # Store agent_id as integer
    }

    if "sentiment_score" in detection:
        details["sentiment_score"] = detection["sentiment_score"]

    with current_app.app_context():
        log_entry = DetectionLog(
            room_url=stream_url,
            event_type="audio_detection",
            details=details,
            timestamp=datetime.now(),
            assigned_agent=agent_id,  # Store agent_id as integer
            assignment_id=assignment_id,
            read=False
        )
        db.session.add(log_entry)
        db.session.commit()

        notification_data = {
            "id": log_entry.id,
            "event_type": log_entry.event_type,
            "timestamp": log_entry.timestamp.isoformat(),
            "details": log_entry.details,
            "read": log_entry.read,
            "room_url": log_entry.room_url,
            "streamer": streamer,
            "platform": platform,
            "assigned_agent": agent_id if agent_id is not None else "Unassigned"  # For display
        }
        emit_notification(notification_data)

# =============== VIDEO PROCESSING ===============
def extract_video_frame(stream_url):
    """Extract single frame from video stream"""
    try:
        container = av.open(stream_url, timeout=30)
        video_stream = next((s for s in container.streams if s.type == 'video'), None)
        
        if not video_stream:
            logger.error(f"No video stream in {stream_url}")
            return None
            
        container.seek(1000000, any_frame=False, backward=True, stream=video_stream)
        
        for frame in container.decode(video_stream):
            img = frame.to_ndarray(format='rgb24')
            return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
        logger.error(f"No frames in {stream_url}")
        return None
        
    except Exception as e:
        logger.error(f"Video frame error: {e}")
        return None

def process_video_frame(frame, stream_url):
    """Detect objects in video frame"""
    model = load_yolo_model()
    if not model:
        return []
    
    flagged = refresh_flagged_objects()
    if not flagged:
        return []
    
    try:
        results = model(frame)
        detections = []
        now = datetime.now()
        
        for result in results:
            for box in result.boxes:
                bbox = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                cls_name = model.names.get(cls_id, str(cls_id)).lower()
                
                if cls_name not in flagged or conf < flagged[cls_name]:
                    continue
                
                if cls_name in last_visual_alerts.get(stream_url, {}):
                    last_alert = last_visual_alerts[stream_url][cls_name]
                    if (now - last_alert).total_seconds() < VISUAL_ALERT_COOLDOWN:
                        continue
                
                last_visual_alerts.setdefault(stream_url, {})[cls_name] = now
                detections.append({
                    "class": cls_name,
                    "confidence": conf,
                    "bbox": bbox.tolist(),
                    "timestamp": now.isoformat()
                })
        
        return detections
    
    except Exception as e:
        logger.error(f"Video processing error: {e}")
        return []

def annotate_frame(frame, detections):
    """Draw detection boxes on frame"""
    annotated = frame.copy()
    for det in detections:
        x1, y1, x2, y2 = map(int, det["bbox"])
        label = f'{det["class"]} {det["confidence"]*100:.1f}%'
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(annotated, label, (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    return annotated

def log_video_detection(detections, frame, stream_url):
    """Log video detections with annotated frame"""
    if not detections:
        return
        
    platform, streamer = get_stream_info(stream_url)
    assignment_id, agent_id = get_stream_assignment(stream_url)
    
    annotated = annotate_frame(frame, detections)
    success, buffer = cv2.imencode('.jpg', annotated)
    if not success:
        logger.error("Frame encoding failed")
        return
        
    image_b64 = base64.b64encode(buffer).decode('utf-8')
    
    details = {
        "detections": detections,
        "timestamp": datetime.now().isoformat(),
        "streamer_name": streamer,
        "platform": platform,
        "annotated_image": image_b64,
        "assigned_agent": agent_id  # Store agent_id as integer
    }
    
    with current_app.app_context():
        log_entry = DetectionLog(
            room_url=stream_url,
            event_type="object_detection",
            details=details,
            detection_image=buffer.tobytes(),
            timestamp=datetime.now(),
            assigned_agent=agent_id,  # Store agent_id as integer
            assignment_id=assignment_id,
            read=False
        )
        db.session.add(log_entry)
        db.session.commit()
        
        notification_data = {
            "id": log_entry.id,
            "event_type": log_entry.event_type,
            "timestamp": log_entry.timestamp.isoformat(),
            "details": log_entry.details,
            "read": log_entry.read,
            "room_url": log_entry.room_url,
            "streamer": streamer,
            "platform": platform,
            "assigned_agent": agent_id if agent_id is not None else "Unassigned"  # For display
        }
        emit_notification(notification_data)

# =============== CHAT PROCESSING ===============
def fetch_chat_messages(stream_url):
    """Fetch chat messages based on platform"""
    platform, streamer = get_stream_info(stream_url)
    
    try:
        if platform == "chaturbate":
            return fetch_chaturbate_chat(stream_url, streamer)
        elif platform == "stripchat":
            return fetch_stripchat_chat(stream_url, streamer)
        else:
            logger.warning(f"Unsupported platform {platform}")
            return []
    except Exception as e:
        logger.error(f"Chat fetch error: {e}")
        return []

def fetch_chaturbate_chat(stream_url, streamer):
    """Fetch Chaturbate chat messages"""
    try:
        from scraping import fetch_chaturbate_chat_history
        room_slug = re.search(r'chaturbate\.com/([^/]+)', stream_url).group(1)
        chat_data = fetch_chaturbate_chat_history(room_slug)
        
        messages = []
        for msg in chat_data:
            msg_data = msg.get("RoomMessageTopic#RoomMessageTopic:0YJW2WC", {})
            if msg_data:
                messages.append({
                    "username": msg_data.get("from_user", {}).get("username", "unknown"),
                    "message": msg_data.get("message", ""),
                    "timestamp": datetime.now().isoformat()
                })
        return messages
        
    except Exception as e:
        logger.error(f"Chaturbate chat error: {e}")
        return []

def fetch_stripchat_chat(stream_url, streamer):
    """Fetch Stripchat chat messages"""
    try:
        from scraping import fetch_stripchat_chat_history
        chat_data = fetch_stripchat_chat_history(stream_url)
        return [{
            "username": msg.get("username", "unknown"),
            "message": msg.get("text", ""),
            "timestamp": msg.get("timestamp", datetime.now().isoformat())
        } for msg in chat_data]
        
    except Exception as e:
        logger.error(f"Stripchat chat error: {e}")
        return []

def process_chat_messages(messages, stream_url):
    """Analyze chat messages for keywords and sentiment"""
    keywords = refresh_flagged_keywords()
    if not keywords:
        return []
    
    detected = []
    now = datetime.now()
    
    for msg in messages:
        text = msg.get("message", "").lower()
        user = msg.get("username", "unknown")
        timestamp = msg.get("timestamp", now.isoformat())
        
        for keyword in keywords:
            if keyword in text:
                if keyword in last_chat_alerts.get(stream_url, {}):
                    last_alert = last_chat_alerts[stream_url][keyword]
                    if (now - last_alert).total_seconds() < CHAT_ALERT_COOLDOWN:
                        continue
                
                last_chat_alerts.setdefault(stream_url, {})[keyword] = now
                detected.append({
                    "type": "keyword",
                    "keyword": keyword,
                    "message": text,
                    "username": user,
                    "timestamp": timestamp
                })
        
        sentiment = _sentiment_analyzer.polarity_scores(text)
        if sentiment['compound'] <= NEGATIVE_SENTIMENT_THRESHOLD:
            sentiment_key = f"_negative_sentiment_{user}"
            if sentiment_key in last_chat_alerts.get(stream_url, {}):
                last_alert = last_chat_alerts[stream_url][sentiment_key]
                if (now - last_alert).total_seconds() < CHAT_ALERT_COOLDOWN:
                        continue
                    
            last_chat_alerts.setdefault(stream_url, {})[sentiment_key] = now
            detected.append({
                "type": "sentiment",
                "message": text,
                "username": user,
                "sentiment_score": sentiment['compound'],
                "timestamp": timestamp
            })
    
    return detected

def log_chat_detection(detections, stream_url):
    """Log chat detections grouped by type"""
    if not detections:
        return
        
    platform, streamer = get_stream_info(stream_url)
    assignment_id, agent_id = get_stream_assignment(stream_url)
    
    grouped = {}
    for det in detections:
        type_key = det.get("type", "unknown")
        grouped.setdefault(type_key, []).append(det)
    
    for type_key, group in grouped.items():
        details = {
            "detections": group,
            "timestamp": datetime.now().isoformat(),
            "streamer_name": streamer,
            "platform": platform,
            "assigned_agent": agent_id  # Store agent_id as integer
        }
        
        event_type = "chat_sentiment_detection" if type_key == "sentiment" else "chat_detection"
        
        with current_app.app_context():
            log_entry = DetectionLog(
                room_url=stream_url,
                event_type=event_type,
                details=details,
                timestamp=datetime.now(),
                assigned_agent=agent_id,  # Store agent_id as integer
                assignment_id=assignment_id,
                read=False
            )
            db.session.add(log_entry)
            db.session.commit()
            
            notification_data = {
                "id": log_entry.id,
                "event_type": log_entry.event_type,
                "timestamp": log_entry.timestamp.isoformat(),
                "details": log_entry.details,
                "read": log_entry.read,
                "room_url": log_entry.room_url,
                "streamer": streamer,
                "platform": platform,
                "assigned_agent": agent_id if agent_id is not None else "Unassigned"  # For display
            }
            emit_notification(notification_data)

def handle_audio_detection(stream_url, transcript, keyword, sentiment_score, platform, streamer_name):
    """Handle audio detection and log to database"""
    try:
        # Get assignment info
        assignment_id, agent_id = get_stream_assignment(stream_url)
        
        # Create detection log in database
        detection_log = DetectionLog(
            event_type='audio_detection',
            room_url=stream_url,
            timestamp=datetime.utcnow(),
            details={
                'transcript': transcript,
                'keyword': keyword,
                'sentiment_score': sentiment_score,
                'platform': platform,
                'streamer_name': streamer_name,
                'assigned_agent': agent_id  # Store agent_id as integer
            },
            read=False,
            assigned_agent=agent_id,  # Store agent_id as integer
            assignment_id=assignment_id
        )
        db.session.add(detection_log)
        db.session.commit()
        
        # Prepare notification data
        notification_data = {
            "id": detection_log.id,
            "event_type": "audio_detection",
            "timestamp": detection_log.timestamp.isoformat(),
            "details": detection_log.details,
            "read": False,
            "room_url": stream_url,
            "streamer": streamer_name,
            "platform": platform,
            "assigned_agent": agent_id if agent_id is not None else "Unassigned"  # For display
        }
        
        # Emit real-time notification
        emit_notification(notification_data)
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error handling audio detection: {str(e)}")
        return False

def handle_visual_detection(stream_url, detections, annotated_image, platform, streamer_name):
    """Handle visual detection and log to database"""
    try:
        # Get assignment info
        assignment_id, agent_id = get_stream_assignment(stream_url)
        
        # Create detection log in database
        detection_log = DetectionLog(
            event_type='object_detection',
            room_url=stream_url,
            timestamp=datetime.utcnow(),
            details={
                'detections': detections,
                'annotated_image': annotated_image,
                'platform': platform,
                'streamer_name': streamer_name,
                'assigned_agent': agent_id  # Store agent_id as integer
            },
            read=False,
            assigned_agent=agent_id,  # Store agent_id as integer
            assignment_id=assignment_id
        )
        db.session.add(detection_log)
        db.session.commit()
        
        # Prepare notification data
        notification_data = {
            "id": detection_log.id,
            "event_type": "object_detection",
            "timestamp": detection_log.timestamp.isoformat(),
            "details": detection_log.details,
            "read": False,
            "room_url": stream_url,
            "streamer": streamer_name,
            "platform": platform,
            "assigned_agent": agent_id if agent_id is not None else "Unassigned"  # For display
        }
        
        # Emit real-time notification
        emit_notification(notification_data)
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error handling visual detection: {str(e)}")
        return False

def handle_chat_detection(stream_url, message, keywords, sender, platform, streamer_name):
    """Handle chat detection and log to database"""
    try:
        # Get assignment info
        assignment_id, agent_id = get_stream_assignment(stream_url)
        
        # Create detection log in database
        detection_log = DetectionLog(
            event_type='chat_detection',
            room_url=stream_url,
            timestamp=datetime.utcnow(),
            details={
                'message': message,
                'keywords': keywords,
                'sender': sender,
                'platform': platform,
                'streamer_name': streamer_name,
                'assigned_agent': agent_id  # Store agent_id as integer
            },
            read=False,
            assigned_agent=agent_id,  # Store agent_id as integer
            assignment_id=assignment_id
        )
        db.session.add(detection_log)
        db.session.commit()
        
        # Prepare notification data
        notification_data = {
            "id": detection_log.id,
            "event_type": "chat_detection",
            "timestamp": detection_log.timestamp.isoformat(),
            "details": detection_log.details,
            "read": False,
            "room_url": stream_url,
            "streamer": streamer_name,
            "platform": platform,
            "assigned_agent": agent_id if agent_id is not None else "Unassigned"  # For display
        }
        
        # Emit real-time notification
        emit_notification(notification_data)
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error handling chat detection: {str(e)}")
        return False

# =============== MAIN MONITORING CONTROL ===============
def process_combined_detection(app, stream_url, cancel_event, poll_interval=60):
    """Main monitoring loop combining all detection types"""
    with app.app_context():  # Wrap the entire function body
        logger.info(f"Starting monitoring for {stream_url}")
        
        # Start real-time audio processing
        audio_cancel = threading.Event()
        audio_thread = threading.Thread(
            target=process_audio_realtime,
            args=(stream_url, audio_cancel),
            daemon=True
        )
        audio_thread.start()
        
        while not cancel_event.is_set():
            try:
                # Video processing
                frame = extract_video_frame(stream_url)
                if frame:
                    detections = process_video_frame(frame, stream_url)
                    if detections:
                        log_video_detection(detections, frame, stream_url)
                
                # Chat processing
                messages = fetch_chat_messages(stream_url)
                if messages:
                    detections = process_chat_messages(messages, stream_url)
                    if detections:
                        log_chat_detection(detections, stream_url)
                
                # Sleep for polling interval
                for _ in range(poll_interval):
                    if cancel_event.is_set():
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Monitoring error for {stream_url}: {e}")
                time.sleep(10)
        
        # Cleanup
        audio_cancel.set()
        if stream_url in stream_processors:
            _, chunker_cancel = stream_processors[stream_url]
            chunker_cancel.set()
            
        logger.info(f"Stopped monitoring {stream_url}")

def start_monitoring(stream):
    """Start monitoring a stream for detections"""
    if not stream:
        logger.error("Stream not provided")
        return False
    with current_app.app_context():
        if stream.is_monitored:
            logger.info(f"Stream already monitored: {stream.room_url}")
            return True
        stream.is_monitored = True
        db.session.commit()
    
    # Determine the streaming URL (prefer m3u8_url)
    if stream.type.lower() == 'chaturbate' and hasattr(stream, 'chaturbate_m3u8_url'):
        stream_url = stream.chaturbate_m3u8_url
    elif stream.type.lower() == 'stripchat' and hasattr(stream, 'stripchat_m3u8_url'):
        stream_url = stream.stripchat_m3u8_url
    else:
        stream_url = stream.room_url  # Fallback to room_url
    
    if not stream_url:
        logger.error(f"No valid URL for stream: {stream.id}")
        return False
    
    logger.info(f"Starting monitoring for {stream_url}")
    cancel_event = threading.Event()
    # Pass the app instance to the thread
    thread = threading.Thread(
        target=process_combined_detection,
        args=(current_app._get_current_object(), stream_url, cancel_event),
        kwargs={'poll_interval': 60}
    )
    thread.daemon = True
    thread.start()
    stream_processors[stream_url] = (cancel_event, thread)
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
    # Determine the streaming URL (consistent with start_monitoring)
    if stream.type.lower() == 'chaturbate' and hasattr(stream, 'chaturbate_m3u8_url'):
        stream_url = stream.chaturbate_m3u8_url
    elif stream.type.lower() == 'stripchat' and hasattr(stream, 'stripchat_m3u8_url'):
        stream_url = stream.stripchat_m3u8_url
    else:
        stream_url = stream.room_url
    
    with current_app.app_context():
        stream.is_monitored = False
        db.session.commit()
    
    if stream_url in stream_processors:
        cancel_event, thread = stream_processors.get(stream_url, (None, None))
        if cancel_event:
            cancel_event.set()
            if thread:
                thread.join(timeout=2.0)
        del stream_processors[stream_url]
    
    logger.info(f"Stopped monitoring {stream_url}")
    emit_stream_update({
        'id': stream.id,
        'url': stream_url,
        'status': 'stopped',
        'type': stream.type
    })

# =============== EXPORTS ===============
__all__ = [
    'start_monitoring',
    'stop_monitoring',
    'process_audio_segment',
    'process_video_frame',
    'process_chat_messages'
]

if __name__ == "__main__":
    print("Livestream monitoring system - import this module to use")