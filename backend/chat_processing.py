import logging
import re
from datetime import datetime, timedelta
from flask import current_app
from models import DetectionLog, Stream, ChaturbateStream, StripchatStream
from extensions import db
from utils.notifications import emit_notification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# External dependencies
_sentiment_analyzer = None
ENABLE_CHAT_MONITORING = None
CHAT_ALERT_COOLDOWN = None
NEGATIVE_SENTIMENT_THRESHOLD = None
last_chat_alerts = {}

def initialize_chat_globals(sentiment_analyzer, enable_chat_monitoring, chat_alert_cooldown, negative_sentiment_threshold):
    """Initialize global variables from monitoring.py"""
    global _sentiment_analyzer, ENABLE_CHAT_MONITORING, CHAT_ALERT_COOLDOWN, NEGATIVE_SENTIMENT_THRESHOLD
    _sentiment_analyzer = sentiment_analyzer
    ENABLE_CHAT_MONITORING = enable_chat_monitoring
    CHAT_ALERT_COOLDOWN = chat_alert_cooldown
    NEGATIVE_SENTIMENT_THRESHOLD = negative_sentiment_threshold

def load_sentiment_analyzer():
    """Load the VADER sentiment analyzer"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        _sentiment_analyzer = SentimentIntensityAnalyzer()
    return _sentiment_analyzer

def refresh_flagged_keywords():
    """Retrieve current flagged keywords from database"""
    with current_app.app_context():
        from models import ChatKeyword
        keywords = [kw.keyword.lower() for kw in ChatKeyword.query.all()]
    logger.debug(f"Retrieved {len(keywords)} flagged keywords")
    return keywords

def get_stream_info(room_url):
    """Identify platform and streamer from URL"""
    with current_app.app_context():
        cb_stream = ChaturbateStream.query.filter_by(chaturbate_m3u8_url=room_url).first()
        if cb_stream:
            return 'chaturbate', cb_stream.streamer_username
        sc_stream = StripchatStream.query.filter_by(stripchat_m3u8_url=room_url).first()
        if sc_stream:
            return 'stripchat', sc_stream.streamer_username
        stream = Stream.query.filter_by(room_url=room_url).first()
        if stream:
            return stream.type.lower(), stream.streamer_username
    return 'unknown', 'unknown'

def get_stream_assignment(room_url):
    """Get assignment info for a stream"""
    from sqlalchemy.orm import joinedload
    with current_app.app_context():
        stream = Stream.query.filter_by(room_url=room_url).first()
        if not stream:
            cb_stream = ChaturbateStream.query.filter_by(chaturbate_m3u8_url=room_url).first()
            if cb_stream:
                stream = Stream.query.get(cb_stream.id)
            else:
                sc_stream = StripchatStream.query.filter_by(stripchat_m3u8_url=room_url).first()
                if sc_stream:
                    stream = Stream.query.get(sc_stream.id)
        
        if not stream:
            logger.warning(f"No stream found for URL: {room_url}")
            return None, None
        
        from models import Assignment
        query = Assignment.query.options(
            joinedload(Assignment.agent),
            joinedload(Assignment.stream)
        ).filter_by(stream_id=stream.id)
        
        assignments = query.all()
        
        if not assignments:
            logger.info(f"No assignments found for stream: {room_url}")
            return None, None
        
        assignment = assignments[0]
        agent_id = assignment.agent_id
        return assignment.id, agent_id

def fetch_chaturbate_chat(room_url, streamer):
    """Fetch Chaturbate chat messages"""
    try:
        from scraping import fetch_chaturbate_chat_history
        room_slug = re.search(r'chaturbate\.com/([^/]+)', room_url).group(1)
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

def fetch_stripchat_chat(room_url, streamer):
    """Fetch Stripchat chat messages"""
    try:
        from scraping import fetch_stripchat_chat_history
        chat_data = fetch_stripchat_chat_history(room_url)
        return [{
            "username": msg.get("username", "unknown"),
            "message": msg.get("text", ""),
            "timestamp": msg.get("timestamp", datetime.now().isoformat())
        } for msg in chat_data]
    except Exception as e:
        logger.error(f"Stripchat chat error: {e}")
        return []

def fetch_chat_messages(room_url):
    """Fetch chat messages based on platform"""
    if not ENABLE_CHAT_MONITORING:
        logger.info(f"Chat monitoring disabled for {room_url}")
        return []
    platform, streamer = get_stream_info(room_url)
    try:
        if platform == "chaturbate":
            return fetch_chaturbate_chat(room_url, streamer)
        elif platform == "stripchat":
            return fetch_stripchat_chat(room_url, streamer)
        else:
            logger.warning(f"Unsupported platform {platform}")
            return []
    except Exception as e:
        logger.error(f"Chat fetch error: {e}")
        return []

def process_chat_messages(messages, room_url):
    """Analyze chat messages for keywords and sentiment"""
    if not ENABLE_CHAT_MONITORING:
        logger.info(f"Chat monitoring disabled for {room_url}")
        return []
    keywords = refresh_flagged_keywords()
    if not keywords:
        return []
    detected = []
    now = datetime.now()
    analyzer = load_sentiment_analyzer()
    for msg in messages:
        text = msg.get("message", "").lower()
        user = msg.get("username", "unknown")
        timestamp = msg.get("timestamp", now.isoformat())
        for keyword in keywords:
            if keyword in text:
                if keyword in last_chat_alerts.get(room_url, {}):
                    last_alert = last_chat_alerts[room_url][keyword]
                    if (now - last_alert).total_seconds() < CHAT_ALERT_COOLDOWN:
                        continue
                last_chat_alerts.setdefault(room_url, {})[keyword] = now
                detected.append({
                    "type": "keyword",
                    "keyword": keyword,
                    "message": text,
                    "username": user,
                    "timestamp": timestamp
                })
        sentiment = analyzer.polarity_scores(text)
        if sentiment['compound'] <= NEGATIVE_SENTIMENT_THRESHOLD:
            sentiment_key = f"_negative_sentiment_{user}"
            if sentiment_key in last_chat_alerts.get(room_url, {}):
                last_alert = last_chat_alerts[room_url][sentiment_key]
                if (now - last_alert).total_seconds() < CHAT_ALERT_COOLDOWN:
                    continue
            last_chat_alerts.setdefault(room_url, {})[sentiment_key] = now
            detected.append({
                "type": "sentiment",
                "message": text,
                "username": user,
                "sentiment_score": sentiment['compound'],
                "timestamp": timestamp
            })
    return detected

def log_chat_detection(detections, room_url):
    """Log chat detections grouped by type"""
    if not ENABLE_CHAT_MONITORING or not detections:
        return
    platform, streamer = get_stream_info(room_url)
    assignment_id, agent_id = get_stream_assignment(room_url)
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
            "assigned_agent": agent_id
        }
        event_type = "chat_sentiment_detection" if type_key == "sentiment" else "chat_detection"
        with current_app.app_context():
            log_entry = DetectionLog(
                room_url=room_url,
                event_type=event_type,
                details=details,
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