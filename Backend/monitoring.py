# monitoring.py
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

from flask import current_app
from models import (
    ChatKeyword, FlaggedObject, DetectionLog, Stream, User, Assignment,
    ChaturbateStream, StripchatStream
)
from extensions import db
from utils.notifications import emit_notification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('monitoring.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global variables and locks
_whisper_model = None
_whisper_lock = threading.Lock()
_yolo_model = None
_yolo_lock = threading.Lock()
_sentiment_analyzer = SentimentIntensityAnalyzer()

# Cooldown periods to prevent duplicate alerts
AUDIO_ALERT_COOLDOWN = 60  # seconds
VISUAL_ALERT_COOLDOWN = 30  # seconds
CHAT_ALERT_COOLDOWN = 45    # seconds

# Tracking variables for alert cooldowns
last_audio_alerts = {}  # {stream_url: {keyword: timestamp}}
last_visual_alerts = {}  # {stream_url: {object_class: timestamp}}
last_chat_alerts = {}    # {stream_url: {keyword: timestamp}}

# Sentiment threshold for negative content
NEGATIVE_SENTIMENT_THRESHOLD = -0.5

# =============== MODEL LOADING FUNCTIONS ===============

def load_whisper_model():
    """Load the OpenAI Whisper model for speech recognition"""
    global _whisper_model
    with _whisper_lock:
        if _whisper_model is None:
            try:
                # Use the "base" model for faster processing
                _whisper_model = whisper.load_model("base")
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading Whisper model: {e}")
                _whisper_model = None
    return _whisper_model

def load_yolo_model():
    """Load the YOLO model for object detection"""
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


# Add this function to your monitoring.py file
def start_notification_monitor():
    """
    Start the notification monitoring system
    
    This function initializes the background processes needed for monitoring notifications
    """
    logger.info("Starting notification monitoring system")
    
    try:
        # Set up any global notification monitoring services
        # This could include:
        # - Connecting to message queues
        # - Setting up webhook listeners
        # - Initializing background tasks
        
        # Just as a placeholder for now, we'll create a basic background thread
        notification_thread = threading.Thread(
            target=notification_monitor_loop,
            daemon=True
        )
        notification_thread.start()
        
        logger.info("Notification monitoring system started successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to start notification monitoring system: {e}")
        return False

def notification_monitor_loop():
    """Background loop for the notification monitor"""
    logger.info("Notification monitor loop started")
    
    while True:
        try:
            # Periodic check for pending notifications
            # This would typically check a queue, database, or external service
            
            # Sleep to avoid high CPU usage
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in notification monitor loop: {e}")
            time.sleep(60)  # Wait a bit after errors

# =============== DATA RETRIEVAL FUNCTIONS ===============

def refresh_flagged_keywords():
    """Retrieve and return a list of chat keywords from the database"""
    with current_app.app_context():
        keywords = [kw.keyword.lower() for kw in ChatKeyword.query.all()]
    logger.info(f"Retrieved {len(keywords)} flagged keywords")
    return keywords

def refresh_flagged_objects():
    """Retrieve and return a dictionary of flagged objects and their confidence thresholds"""
    with current_app.app_context():
        objects = FlaggedObject.query.all()
        flagged = {obj.object_name.lower(): float(obj.confidence_threshold) for obj in objects}
    logger.info(f"Retrieved {len(flagged)} flagged objects")
    return flagged

def get_stream_info(stream_url):
    """Get platform and streamer info for a stream URL"""
    with current_app.app_context():
        # Try to find in Chaturbate streams
        cb_stream = ChaturbateStream.query.filter_by(chaturbate_m3u8_url=stream_url).first()
        if cb_stream:
            return 'chaturbate', cb_stream.streamer_username
            
        # Try to find in Stripchat streams
        sc_stream = StripchatStream.query.filter_by(stripchat_m3u8_url=stream_url).first()
        if sc_stream:
            return 'stripchat', sc_stream.streamer_username
            
        # Try generic stream
        stream = Stream.query.filter_by(room_url=stream_url).first()
        if stream:
            return stream.type.lower(), stream.streamer_username
            
    return 'unknown', 'unknown'

def get_stream_assignment(stream_url):
    """Get assignment information for a stream URL"""
    with current_app.app_context():
        stream = Stream.query.filter_by(room_url=stream_url).first()
        if not stream:
            return None, None
            
        assignment = Assignment.query.filter_by(stream_id=stream.id).first()
        if assignment and assignment.agent:
            return assignment.id, assignment.agent_username
        
    return None, None

# =============== AUDIO MONITORING FUNCTIONS ===============

def setup_audio_monitoring(stream_url):
    """Initialize audio monitoring for a stream"""
    model = load_whisper_model()
    if not model:
        logger.error("Failed to load Whisper model for audio monitoring")
        return False
        
    # Initialize cooldown tracking for this stream
    if stream_url not in last_audio_alerts:
        last_audio_alerts[stream_url] = {}
        
    return True

def process_audio_segment(audio_data, stream_url):
    """
    Process an audio segment using OpenAI Whisper
    
    Args:
        audio_data: Raw audio data bytes or numpy array
        stream_url: URL of the stream being monitored
        
    Returns:
        List of detected flagged keywords
    """
    model = load_whisper_model()
    if not model:
        return []
    
    # Get flagged keywords
    keywords = refresh_flagged_keywords()
    if not keywords:
        return []
    
    try:
        # Convert audio to format expected by Whisper
        # This assumes audio_data is in the format expected by Whisper
        result = model.transcribe(audio_data, language="en")
        transcript = result["text"]
        
        # Skip empty transcripts
        if not transcript.strip():
            return []
            
        # Check for flagged keywords in transcript
        detected_keywords = []
        for keyword in keywords:
            if keyword.lower() in transcript.lower():
                # Check if we're in cooldown period for this keyword
                now = datetime.now()
                if keyword in last_audio_alerts.get(stream_url, {}):
                    last_alert = last_audio_alerts[stream_url][keyword]
                    if (now - last_alert).total_seconds() < AUDIO_ALERT_COOLDOWN:
                        continue  # Skip, in cooldown
                
                # Update last alert time
                if stream_url not in last_audio_alerts:
                    last_audio_alerts[stream_url] = {}
                last_audio_alerts[stream_url][keyword] = now
                
                detected_keywords.append({
                    "keyword": keyword,
                    "transcript": transcript,
                    "timestamp": now.isoformat()
                })
                
        # Perform sentiment analysis
        sentiment = _sentiment_analyzer.polarity_scores(transcript)
        compound_score = sentiment['compound']
        
        # Check for negative sentiment
        if compound_score <= NEGATIVE_SENTIMENT_THRESHOLD:
            # Ensure we're not in cooldown for negative sentiment
            now = datetime.now()
            sentiment_key = "_negative_sentiment_"
            if sentiment_key in last_audio_alerts.get(stream_url, {}):
                last_alert = last_audio_alerts[stream_url][sentiment_key]
                if (now - last_alert).total_seconds() < AUDIO_ALERT_COOLDOWN:
                    return detected_keywords  # Skip sentiment alert, in cooldown
                    
            # Update last alert time for sentiment
            if stream_url not in last_audio_alerts:
                last_audio_alerts[stream_url] = {}
            last_audio_alerts[stream_url][sentiment_key] = now
            
            detected_keywords.append({
                "keyword": "negative_sentiment",
                "transcript": transcript,
                "sentiment_score": compound_score,
                "timestamp": now.isoformat()
            })
            
        return detected_keywords
            
    except Exception as e:
        logger.error(f"Error in audio processing: {e}")
        return []

def log_audio_detection(detection, stream_url):
    """Log audio detection events to the database"""
    platform, streamer_name = get_stream_info(stream_url)
    assignment_id, assigned_agent = get_stream_assignment(stream_url)
    
    # Format the detection details
    keyword = detection.get("keyword")
    transcript = detection.get("transcript")
    sentiment_score = detection.get("sentiment_score", None)
    
    details = {
        "keyword": keyword,
        "transcript": transcript,
        "timestamp": detection.get("timestamp"),
        "streamer_name": streamer_name,
        "platform": platform,
        "assigned_agent": assigned_agent or "Unassigned"
    }
    
    if sentiment_score is not None:
        details["sentiment_score"] = sentiment_score
    
    with current_app.app_context():
        log_entry = DetectionLog(
            room_url=stream_url,
            event_type="audio_detection",
            details=details,
            timestamp=datetime.now(),
            assigned_agent=assigned_agent,
            assignment_id=assignment_id,
            read=False
        )
        db.session.add(log_entry)
        db.session.commit()
        
        # Create notification data
        notification_data = {
            "id": log_entry.id,
            "event_type": log_entry.event_type,
            "timestamp": log_entry.timestamp.isoformat(),
            "details": log_entry.details,
            "read": log_entry.read,
            "room_url": log_entry.room_url,
            "streamer": streamer_name,
            "platform": platform,
            "assigned_agent": assigned_agent or "Unassigned"
        }
        
        # Emit notification
        emit_notification(notification_data)

def handle_audio_detection(stream_url, transcript, keyword, sentiment_score, platform, streamer_name):
    try:
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
                'streamer_name': streamer_name
            },
            read=False
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
            "assigned_agent": detection_log.details.get('assigned_agent', 'Unassigned')
        }
        
        # Emit real-time notification
        emit_notification(notification_data)
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error handling audio detection: {str(e)}")
        return False

# =============== VIDEO MONITORING FUNCTIONS ===============

def setup_video_monitoring(stream_url):
    """Initialize video monitoring for a stream"""
    model = load_yolo_model()
    if not model:
        logger.error("Failed to load YOLO model for video monitoring")
        return False
    
    # Initialize cooldown tracking for this stream
    if stream_url not in last_visual_alerts:
        last_visual_alerts[stream_url] = {}
        
    return True

def process_video_frame(frame, stream_url):
    """
    Process a video frame using YOLO for object detection
    
    Args:
        frame: OpenCV image (numpy array)
        stream_url: URL of the stream being monitored
        
    Returns:
        List of detected objects with confidence scores
    """
    model = load_yolo_model()
    if model is None:
        return []
    
    # Get flagged objects with confidence thresholds
    flagged_objects = refresh_flagged_objects()
    if not flagged_objects:
        return []
    
    try:
        # Run detection on frame
        results = model(frame)
        
        # Extract detections 
        detections = []
        for result in results:
            for box in result.boxes:
                bbox = box.xyxy.cpu().numpy()[0]
                confidence = float(box.conf.cpu().numpy()[0])
                class_id = int(box.cls.cpu().numpy()[0])
                object_class = model.names.get(class_id, str(class_id)).lower()
                
                # Skip if not in flagged objects or below threshold
                if object_class not in flagged_objects:
                    continue
                
                threshold = flagged_objects[object_class]
                if confidence < threshold:
                    continue
                
                # Check if we're in cooldown period for this object class
                now = datetime.now()
                if object_class in last_visual_alerts.get(stream_url, {}):
                    last_alert = last_visual_alerts[stream_url][object_class]
                    if (now - last_alert).total_seconds() < VISUAL_ALERT_COOLDOWN:
                        continue  # Skip, in cooldown
                
                # Update last alert time
                if stream_url not in last_visual_alerts:
                    last_visual_alerts[stream_url] = {}
                last_visual_alerts[stream_url][object_class] = now
                
                # Add to detections
                x1, y1, x2, y2 = bbox
                detections.append({
                    "class": object_class,
                    "confidence": confidence,
                    "bbox": [int(x1), int(y1), int(x2 - x1), int(y2 - y1)],
                    "timestamp": now.isoformat()
                })
        
        return detections
    
    except Exception as e:
        logger.error(f"Error in video processing: {e}")
        return []

def annotate_frame(frame, detections):
    """Annotate frame with bounding boxes for detected objects"""
    annotated_frame = frame.copy()
    for det in detections:
        x, y, w, h = det["bbox"]
        label = f'{det["class"]} ({det["confidence"]*100:.1f}%)'
        # Draw red rectangle
        cv2.rectangle(annotated_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
        # Add label with white text on red background
        cv2.putText(annotated_frame, label, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    return annotated_frame

def log_video_detection(detections, frame, stream_url):
    """Log video detection events to the database"""
    if not detections:
        return
        
    platform, streamer_name = get_stream_info(stream_url)
    assignment_id, assigned_agent = get_stream_assignment(stream_url)
    
    # Annotate frame with detections
    annotated_frame = annotate_frame(frame, detections)
    
    # Convert frame to JPEG
    success, buffer = cv2.imencode('.jpg', annotated_frame)
    if not success:
        logger.error("Failed to encode annotated frame")
        return
        
    image_data = buffer.tobytes()
    image_b64 = base64.b64encode(image_data).decode('utf-8') if image_data else None
    
    # Format the detection details
    details = {
        "detections": detections,
        "timestamp": datetime.now().isoformat(),
        "streamer_name": streamer_name,
        "platform": platform,
        "annotated_image": image_b64,
        "assigned_agent": assigned_agent or "Unassigned"
    }
    
    with current_app.app_context():
        log_entry = DetectionLog(
            room_url=stream_url,
            event_type="object_detection",
            details=details,
            detection_image=image_data,
            timestamp=datetime.now(),
            assigned_agent=assigned_agent,
            assignment_id=assignment_id,
            read=False
        )
        db.session.add(log_entry)
        db.session.commit()
        
        # Create notification data
        notification_data = {
            "id": log_entry.id,
            "event_type": log_entry.event_type,
            "timestamp": log_entry.timestamp.isoformat(),
            "details": log_entry.details,
            "read": log_entry.read,
            "room_url": log_entry.room_url,
            "streamer": streamer_name,
            "platform": platform,
            "assigned_agent": assigned_agent or "Unassigned"
        }
        
        # Emit notification
        emit_notification(notification_data)

def handle_visual_detection(stream_url, detections, annotated_image, platform, streamer_name):
    try:
        # Create detection log in database
        detection_log = DetectionLog(
            event_type='object_detection',
            room_url=stream_url,
            timestamp=datetime.utcnow(),
            details={
                'detections': detections,
                'annotated_image': annotated_image,
                'platform': platform,
                'streamer_name': streamer_name
            },
            read=False
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
            "assigned_agent": detection_log.details.get('assigned_agent', 'Unassigned')
        }
        
        # Emit real-time notification
        emit_notification(notification_data)
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error handling visual detection: {str(e)}")
        return False

# =============== CHAT MONITORING FUNCTIONS ===============

def setup_chat_monitoring(stream_url):
    """Initialize chat monitoring for a stream"""
    # Initialize cooldown tracking for this stream
    if stream_url not in last_chat_alerts:
        last_chat_alerts[stream_url] = {}
        
    return True

def fetch_chat_messages(stream_url):
    """
    Fetch chat messages from Chaturbate or Stripchat
    
    Args:
        stream_url: URL of the stream to monitor
        
    Returns:
        List of chat messages in the format:
        [{"username": "user", "message": "text", "timestamp": "iso_time"}]
    """
    platform, streamer = get_stream_info(stream_url)
    
    try:
        # Determine which platform to scrape
        if platform == "chaturbate":
            return fetch_chaturbate_chat(stream_url, streamer)
        elif platform == "stripchat":
            return fetch_stripchat_chat(stream_url, streamer)
        else:
            logger.warning(f"Unsupported platform {platform} for chat monitoring")
            return []
    except Exception as e:
        logger.error(f"Error fetching chat messages: {e}")
        return []

def fetch_chaturbate_chat(stream_url, streamer):
    """Fetch chat messages from Chaturbate"""
    # Extract room slug from URL
    match = re.search(r'chaturbate\.com/([^/]+)', stream_url)
    if not match:
        logger.error(f"Could not extract room slug from {stream_url}")
        return []
        
    room_slug = match.group(1)
    
    try:
        # Import scraping module at the time of use
        from scraping import fetch_chaturbate_chat_history
        
        # Fetch chat history
        chat_data = fetch_chaturbate_chat_history(room_slug)
        
        # Process the chat data into a standard format
        messages = []
        for msg in chat_data:
            msg_data = msg.get("RoomMessageTopic#RoomMessageTopic:0YJW2WC", {})
            if not msg_data:
                continue
                
            message = msg_data.get("message", "")
            sender = msg_data.get("from_user", {}).get("username", "unknown")
            timestamp = datetime.now().isoformat()  # Chaturbate doesn't provide timestamps
            
            messages.append({
                "username": sender,
                "message": message,
                "timestamp": timestamp
            })
            
        return messages
        
    except Exception as e:
        logger.error(f"Error fetching Chaturbate chat: {e}")
        return []

def fetch_stripchat_chat(stream_url, streamer):
    """Fetch chat messages from Stripchat"""
    try:
        # Import scraping module at the time of use
        from scraping import fetch_stripchat_chat_history
        
        # Fetch chat history
        chat_data = fetch_stripchat_chat_history(stream_url)
        
        # Process the chat data into a standard format
        messages = []
        for msg in chat_data:
            sender = msg.get("username", "unknown")
            message = msg.get("text", "")
            timestamp = msg.get("timestamp", datetime.now().isoformat())
            
            messages.append({
                "username": sender,
                "message": message,
                "timestamp": timestamp
            })
            
        return messages
        
    except Exception as e:
        logger.error(f"Error fetching Stripchat chat: {e}")
        return []

def process_chat_messages(messages, stream_url):
    """
    Process chat messages to detect flagged keywords and negative sentiment
    
    Args:
        messages: List of chat messages
        stream_url: URL of the stream
        
    Returns:
        List of detected issues in chat
    """
    # Get flagged keywords
    keywords = refresh_flagged_keywords()
    if not keywords:
        return []
    
    detected_issues = []
    now = datetime.now()
    
    for message in messages:
        text = message.get("message", "").lower()
        username = message.get("username", "unknown")
        timestamp = message.get("timestamp", now.isoformat())
        
        # Check for flagged keywords
        for keyword in keywords:
            if keyword.lower() in text:
                # Check if we're in cooldown period for this keyword
                if keyword in last_chat_alerts.get(stream_url, {}):
                    last_alert = last_chat_alerts[stream_url][keyword]
                    if (now - last_alert).total_seconds() < CHAT_ALERT_COOLDOWN:
                        continue  # Skip, in cooldown
                
                # Update last alert time
                if stream_url not in last_chat_alerts:
                    last_chat_alerts[stream_url] = {}
                last_chat_alerts[stream_url][keyword] = now
                
                # Add to detected issues
                detected_issues.append({
                    "type": "keyword",
                    "keyword": keyword,
                    "message": text,
                    "username": username,
                    "timestamp": timestamp
                })
        
        # Perform sentiment analysis
        sentiment = _sentiment_analyzer.polarity_scores(text)
        compound_score = sentiment['compound']
        
        # Check for negative sentiment
        if compound_score <= NEGATIVE_SENTIMENT_THRESHOLD:
            # Ensure we're not in cooldown for negative sentiment
            sentiment_key = f"_negative_sentiment_{username}"
            if sentiment_key in last_chat_alerts.get(stream_url, {}):
                last_alert = last_chat_alerts[stream_url][sentiment_key]
                if (now - last_alert).total_seconds() < CHAT_ALERT_COOLDOWN:
                    continue  # Skip sentiment alert, in cooldown
                    
            # Update last alert time for sentiment
            if stream_url not in last_chat_alerts:
                last_chat_alerts[stream_url] = {}
            last_chat_alerts[stream_url][sentiment_key] = now
            
            detected_issues.append({
                "type": "sentiment",
                "message": text,
                "username": username,
                "sentiment_score": compound_score,
                "timestamp": timestamp
            })
    
    return detected_issues

def log_chat_detection(detections, stream_url):
    """Log chat detection events to the database"""
    if not detections:
        return
        
    platform, streamer_name = get_stream_info(stream_url)
    assignment_id, assigned_agent = get_stream_assignment(stream_url)
    
    # Group detections by type
    grouped = {}
    for detection in detections:
        type_key = detection.get("type", "unknown")
        if type_key not in grouped:
            grouped[type_key] = []
        grouped[type_key].append(detection)
    
    # Log each type separately
    for type_key, group in grouped.items():
        # Format the detection details
        details = {
            "detections": group,
            "timestamp": datetime.now().isoformat(),
            "streamer_name": streamer_name,
            "platform": platform,
            "assigned_agent": assigned_agent or "Unassigned"
        }
        
        event_type = "chat_detection"
        if type_key == "sentiment":
            event_type = "chat_sentiment_detection"
        
        with current_app.app_context():
            log_entry = DetectionLog(
                room_url=stream_url,
                event_type=event_type,
                details=details,
                timestamp=datetime.now(),
                assigned_agent=assigned_agent,
                assignment_id=assignment_id,
                read=False
            )
            db.session.add(log_entry)
            db.session.commit()
            
            # Create notification data
            notification_data = {
                "id": log_entry.id,
                "event_type": log_entry.event_type,
                "timestamp": log_entry.timestamp.isoformat(),
                "details": log_entry.details,
                "read": log_entry.read,
                "room_url": log_entry.room_url,
                "streamer": streamer_name,
                "platform": platform,
                "assigned_agent": assigned_agent or "Unassigned"
            }
            
            # Emit notification
            emit_notification(notification_data)

def handle_chat_detection(stream_url, message, keywords, sender, platform, streamer_name):
    try:
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
                'streamer_name': streamer_name
            },
            read=False
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
            "assigned_agent": detection_log.details.get('assigned_agent', 'Unassigned')
        }
        
        # Emit real-time notification
        emit_notification(notification_data)
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error handling chat detection: {str(e)}")
        return False

# =============== MAIN MONITORING FUNCTIONS ===============

def extract_audio_from_stream(stream_url, duration=10):
    """
    Extract audio segments from an HLS stream
    
    Args:
        stream_url: URL of the HLS stream
        duration: Number of seconds of audio to extract
        
    Returns:
        Audio data in format compatible with Whisper
    """
    try:
        # Use PyAV to extract audio from HLS
        container = av.open(stream_url, timeout=30)
        audio_stream = next((s for s in container.streams if s.type == 'audio'), None)
        
        if not audio_stream:
            logger.error(f"No audio stream found in {stream_url}")
            return None
            
        # Set up resampler for whisper compatible format (16kHz mono)
        resampler = av.AudioResampler(
            format='s16', 
            layout='mono', 
            rate=16000
        )
        
        # Calculate how many audio frames to process
        audio_frames = []
        start_time = time.time()
        
        # Read audio frames for the specified duration
        for frame in container.decode(audio_stream):
            # Resample frame
            frames = resampler.resample(frame)
            for frame in frames:
                audio_frames.append(frame)
            
            # Check if we've collected enough audio
            if time.time() - start_time >= duration:
                break
        
        if not audio_frames:
            logger.error(f"No audio frames extracted from {stream_url}")
            return None
            
        # Convert frames to numpy array for Whisper
        audio_data = np.concatenate([frame.to_ndarray() for frame in audio_frames])
        audio_data = audio_data.astype(np.float32) / 32768.0  # Convert to float [-1.0, 1.0]
        
        return audio_data
        
    except Exception as e:
        logger.error(f"Error extracting audio from stream: {e}")
        return None

def extract_video_frame(stream_url):
    """
    Extract a video frame from an HLS stream
    
    Args:
        stream_url: URL of the HLS stream
        
    Returns:
        OpenCV image (numpy array)
    """
    try:
        # Use PyAV to extract video frame from HLS
        container = av.open(stream_url, timeout=30)
        video_stream = next((s for s in container.streams if s.type == 'video'), None)
        
        if not video_stream:
            logger.error(f"No video stream found in {stream_url}")
            return None
            
        # Seek to a point with a keyframe
        container.seek(1000000, any_frame=False, backward=True, stream=video_stream)
        
        # Read frames until we get one
        for frame in container.decode(video_stream):
            # Convert PyAV frame to numpy array for OpenCV
            img = frame.to_ndarray(format='rgb24')
            # Convert RGB to BGR for OpenCV
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            return img
            
        logger.error(f"No video frames extracted from {stream_url}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting video frame from stream: {e}")
        return None

# In monitoring.py or appropriate file
def process_combined_detection(stream_url, cancel_event, poll_interval=60):
    """
    Process audio, video, and chat detection for a stream
    
    Args:
        stream_url: URL of the HLS stream
        cancel_event: Threading event to signal cancellation
        poll_interval: How often to poll the stream (seconds)
    """
    logger.info(f"Starting combined detection for {stream_url}")
    
    # Setup each monitoring component
    audio_setup = setup_audio_monitoring(stream_url)
    video_setup = setup_video_monitoring(stream_url)
    chat_setup = setup_chat_monitoring(stream_url)
    
    if not (audio_setup and video_setup and chat_setup):
        logger.error(f"Failed to set up monitoring for {stream_url}")
        return
    
    while not cancel_event.is_set():
        try:
            # Process video frame for object detection
            frame = extract_video_frame(stream_url)
            if frame is not None:
                video_detections = process_video_frame(frame, stream_url)
                if video_detections:
                    log_video_detection(video_detections, frame, stream_url)
                    logger.info(f"Detected {len(video_detections)} objects in {stream_url}")
            
            # Process audio for speech recognition
            audio_data = extract_audio_from_stream(stream_url)
            if audio_data is not None:
                audio_detections = process_audio_segment(audio_data, stream_url)
                for detection in audio_detections:
                    log_audio_detection(detection, stream_url)
                if audio_detections:
                    logger.info(f"Detected {len(audio_detections)} audio issues in {stream_url}")
            
            # Process chat messages
            messages = fetch_chat_messages(stream_url)
            if messages:
                chat_detections = process_chat_messages(messages, stream_url)
                if chat_detections:
                    log_chat_detection(chat_detections, stream_url)
                    logger.info(f"Detected {len(chat_detections)} chat issues in {stream_url}")
            
            # Wait for the next polling interval
            for _ in range(poll_interval):
                if cancel_event.is_set():
                    break
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in combined detection loop: {e}")
            # Wait a bit and continue
            time.sleep(10)
    
    logger.info(f"Stopped combined detection for {stream_url}")        
def start_monitoring(stream_url):
    """
    Start monitoring a stream for audio, video, and chat content
    
    Args:
        stream_url: URL of the HLS stream
        
    Returns:
        Tuple of (cancel_event, threads)
    """
    logger.info(f"Starting monitoring for {stream_url}")
    
    # Create cancel event
    cancel_event = threading.Event()
    
    # Create and start the detection thread
    detection_thread = threading.Thread(
        target=process_combined_detection,
        args=(stream_url, cancel_event),
        daemon=True
    )
    detection_thread.start()
    
    return cancel_event, detection_thread

def stop_monitoring(stream_url, cancel_event=None, thread=None):
    """Stop monitoring a stream"""
    if cancel_event:
        cancel_event.set()
    
    if thread and thread.is_alive():
        thread.join(timeout=5)
        
    logger.info(f"Stopped monitoring for {stream_url}")

# =============== EXPORTS ===============

# Export for route usage
__all__ = [
    'start_monitoring',
    'stop_monitoring',
    'process_audio_segment',
    'process_video_frame',
    'process_chat_messages'
]

if __name__ == "__main__":
    # Example usage
    print("Livestream monitoring system - import this module to use")