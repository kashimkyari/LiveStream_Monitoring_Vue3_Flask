import logging
import cv2
import numpy as np
from datetime import datetime, timedelta
from flask import current_app
from models import DetectionLog, Stream, ChaturbateStream, StripchatStream
from extensions import db
from utils.notifications import emit_notification
from dotenv import load_dotenv
import base64
import os
import threading

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# External dependencies
_yolo_model = None
_yolo_lock = threading.Lock()  # Initialize the lock with a proper threading.Lock object
last_visual_alerts = {}

def initialize_video_globals(yolo_model=None, yolo_lock=None):
    """Initialize global variables for YOLO model and lock"""
    global _yolo_model, _yolo_lock
    _yolo_model = yolo_model
    if yolo_lock is not None:
        _yolo_lock = yolo_lock
    else:
        # Ensure _yolo_lock is always a valid lock object
        _yolo_lock = threading.Lock()
    logger.info("Video globals initialized")

def load_yolo_model():
    """Load the YOLO object detection model"""
    logger.debug(f"Checking video monitoring: {current_app.config['ENABLE_VIDEO_MONITORING']}")
    if not current_app.config['ENABLE_VIDEO_MONITORING']:
        logger.info("Video monitoring disabled; skipping YOLO model loading")
        return None
    global _yolo_model
    
    global _yolo_model  # This global declaration is already here
    # Ensure _yolo_lock is not None before using it
    if _yolo_lock is None:
        logger.warning("YOLO lock was None, creating a new lock")
        # Don't redeclare global _yolo_lock here as it's already a global variable
        _yolo_lock = threading.Lock()
        
    with _yolo_lock:
        if _yolo_model is None:
            try:
                from ultralytics import YOLO
                _yolo_model = YOLO("YOLO11m-seg.pt", verbose=False)
                _yolo_model.verbose = False
                logger.info("YOLO model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading YOLO model: {e}")
                _yolo_model = None
    return _yolo_model

def refresh_flagged_objects():
    """Retrieve flagged objects and confidence thresholds"""
    with current_app.app_context():
        from models import FlaggedObject
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

def get_stream_assignment(stream_url):
    """Get assignment info for a stream"""
    from sqlalchemy.orm import joinedload
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
        
        from models import Assignment
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
        return assignment.id, agent_id

def process_video_frame(frame, stream_url):
    """Detect objects in video frame"""
    if not current_app.config['ENABLE_VIDEO_MONITORING']:
        logger.info(f"Video monitoring disabled for {stream_url}")
        return []
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
                    if (now - last_alert).total_seconds() < current_app.config['VISUAL_ALERT_COOLDOWN']:
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
    if not current_app.config['ENABLE_VIDEO_MONITORING'] or not detections:
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
        "assigned_agent": agent_id
    }
    with current_app.app_context():
        log_entry = DetectionLog(
            room_url=stream_url,
            event_type="object_detection",
            details=details,
            detection_image=buffer.tobytes(),
            timestamp=datetime.now(),
            assigned_agent=agent_id,
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
            "assigned_agent": "Unassigned" if not agent_id else "Agent"
        }
        emit_notification(notification_data)