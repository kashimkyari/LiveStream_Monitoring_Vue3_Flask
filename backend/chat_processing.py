import logging
import re
import requests
from datetime import datetime, timedelta
from flask import current_app
from models import DetectionLog, Stream, ChaturbateStream, StripchatStream
from extensions import db
from utils.notifications import emit_notification
import random
import time
from gevent.lock import Semaphore
import urllib3
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Proxy configuration
PROXY_LIST = []
PROXY_LIST_LAST_UPDATED = None
PROXY_LOCK = Semaphore()
PROXY_UPDATE_INTERVAL = 3600
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# External dependencies
_sentiment_analyzer = None
ENABLE_CHAT_MONITORING = None
CHAT_ALERT_COOLDOWN = None
NEGATIVE_SENTIMENT_THRESHOLD = None
last_chat_alerts = {}

def initialize_chat_globals(sentiment_analyzer=None, enable_chat_monitoring=None, chat_alert_cooldown=None, negative_sentiment_threshold=None):
    """Initialize global variables from environment"""
    global _sentiment_analyzer, ENABLE_CHAT_MONITORING, CHAT_ALERT_COOLDOWN, NEGATIVE_SENTIMENT_THRESHOLD
    ENABLE_CHAT_MONITORING = enable_chat_monitoring if enable_chat_monitoring is not None else os.getenv('ENABLE_CHAT_MONITORING', 'true').lower() == 'true'
    CHAT_ALERT_COOLDOWN = chat_alert_cooldown if chat_alert_cooldown is not None else int(os.getenv('CHAT_ALERT_COOLDOWN', 60))
    NEGATIVE_SENTIMENT_THRESHOLD = negative_sentiment_threshold if negative_sentiment_threshold is not None else float(os.getenv('NEGATIVE_SENTIMENT_THRESHOLD', -0.5))
    _sentiment_analyzer = sentiment_analyzer if sentiment_analyzer is not None else load_sentiment_analyzer()

def load_sentiment_analyzer():
    """Load the VADER sentiment analyzer"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        _sentiment_analyzer = SentimentIntensityAnalyzer()
    return _sentiment_analyzer

def update_proxy_list():
    """Fetch fresh proxies from free API services"""
    try:
        response = requests.get(
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            timeout=15
        )
        if response.status_code == 200 and response.text:
            proxies = [proxy.strip() for proxy in response.text.split('\n') if proxy.strip()]
            if len(proxies) > 20:
                return proxies
                
        response = requests.get(
            "https://www.proxy-list.download/api/v1/get?type=http",
            timeout=15
        )
        if response.status_code == 200 and response.text:
            proxies = [proxy.strip() for proxy in response.text.split('\n') if proxy.strip()]
            if len(proxies) > 20:
                return proxies
                
        return None
    except Exception as e:
        logger.error(f"Failed to update proxy list: {str(e)}")
        return None

def get_random_proxy():
    """Select a random proxy from the proxy list, refreshing if needed."""
    global PROXY_LIST, PROXY_LIST_LAST_UPDATED
    
    with PROXY_LOCK:
        current_time = time.time()
        if not PROXY_LIST or not PROXY_LIST_LAST_UPDATED or \
           current_time - PROXY_LIST_LAST_UPDATED > PROXY_UPDATE_INTERVAL:
            new_proxies = update_proxy_list()
            
            if new_proxies and len(new_proxies) >= 10:
                PROXY_LIST = new_proxies
                PROXY_LIST_LAST_UPDATED = current_time
                logger.info(f"Updated proxy list with {len(PROXY_LIST)} proxies")
            elif not PROXY_LIST:
                PROXY_LIST = [
                    "52.67.10.183:80",
                    "200.250.131.218:80",
                ]
                logger.warning("Using static proxy list as fallback")
    
    if PROXY_LIST:
        proxy = random.choice(PROXY_LIST)
        return {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
    return None

def refresh_flagged_keywords():
    """Retrieve current flagged keywords from database"""
    with current_app.app_context():
        from models import ChatKeyword
        keywords = [kw.keyword.lower() for kw in ChatKeyword.query.all()]
    logger.debug(f"Retrieved {len(keywords)} flagged keywords")
    return keywords

def get_stream_info(room_url):
    """Identify platform, streamer, and broadcaster UID from URL, prioritizing room_url"""
    with current_app.app_context():
        # First, try matching the room_url directly in the streams table
        stream = Stream.query.filter_by(room_url=room_url).first()
        if stream:
            logger.debug(f"Found stream by room_url: {room_url}, type: {stream.type}, username: {stream.streamer_username}")
            # For Chaturbate, fetch broadcaster_uid from ChaturbateStream
            if stream.type.lower() == 'chaturbate':
                cb_stream = ChaturbateStream.query.filter_by(id=stream.id).first()
                broadcaster_uid = cb_stream.broadcaster_uid if cb_stream else None
                return stream.type.lower(), stream.streamer_username, broadcaster_uid
            return stream.type.lower(), stream.streamer_username, None
        
        # Fallback to checking m3u8 URLs (for video/audio monitoring scenarios)
        cb_stream = ChaturbateStream.query.filter_by(chaturbate_m3u8_url=room_url).first()
        if cb_stream:
            stream = Stream.query.get(cb_stream.id)
            logger.debug(f"Found stream by chaturbate_m3u8_url: {room_url}, type: chaturbate, username: {stream.streamer_username}")
            return 'chaturbate', stream.streamer_username, cb_stream.broadcaster_uid
        
        sc_stream = StripchatStream.query.filter_by(stripchat_m3u8_url=room_url).first()
        if sc_stream:
            stream = Stream.query.get(sc_stream.id)
            logger.debug(f"Found stream by stripchat_m3u8_url: {room_url}, type: stripchat, username: {stream.streamer_username}")
            return 'stripchat', stream.streamer_username, None
        
        logger.warning(f"No stream found for URL: {room_url}")
        return 'unknown', 'unknown', None

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

def fetch_chaturbate_room_uid(streamer_username):
    """Fetch Chaturbate room UID and broadcaster UID"""
    url = f"https://chaturbate.com/api/chatvideocontext/{streamer_username}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': f'https://chaturbate.com/{streamer_username}/',
        'Connection': 'keep-alive',
    }
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        proxy_dict = get_random_proxy()
        try:
            response = requests.get(
                url,
                headers=headers,
                proxies=proxy_dict,
                timeout=10,
                verify=False
            )
            response.raise_for_status()
            data = response.json()
            broadcaster_uid = data.get('broadcaster_uid')
            room_uid = data.get('room_uid')
            logger.debug(f"Fetched Chaturbate UIDs for {streamer_username}: broadcaster_uid={broadcaster_uid}, room_uid={room_uid}")
            return broadcaster_uid, room_uid
        except Exception as e:
            attempts += 1
            logger.warning(f"Attempt {attempts} failed for Chaturbate room UID fetch for {streamer_username}: {e}")
            if attempts < max_attempts:
                time.sleep(1)
    logger.error(f"Failed to fetch Chaturbate room UID for {streamer_username} after {max_attempts} attempts")
    return None, None

def fetch_chaturbate_chat(room_url, streamer, broadcaster_uid):
    """Fetch Chaturbate chat messages using proxies"""
    if not broadcaster_uid:
        logger.warning(f"No broadcaster UID for {room_url}")
        return []
    url = "https://chaturbate.com/push_service/room_history/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': f'https://chaturbate.com/{streamer}/',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'multipart/form-data; boundary=----geckoformboundary428c342290b0a9092e9dcf7e4e1d5b9',
        'Origin': 'https://chaturbate.com',
        'Connection': 'keep-alive',
    }
    data = (
        '------geckoformboundary428c342290b0a9092e9dcf7e4e1d5b9\r\n'
        f'Content-Disposition: form-data; name="topics"\r\n\r\n'
        f'{{"RoomMessageTopic#RoomMessageTopic:{broadcaster_uid}":{{"broadcaster_uid":"{broadcaster_uid}"}}}}\r\n'
        '------geckoformboundary428c342290b0a9092e9dcf7e4e1d5b9\r\n'
        'Content-Disposition: form-data; name="csrfmiddlewaretoken"\r\n\r\n'
        'NdFODN04i4jCUKVTPs3JyAwxsVnuxiy0\r\n'
        '------geckoformboundary428c342290b0a9092e9dcf7e4e1d5b9--\r\n'
    )
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        proxy_dict = get_random_proxy()
        try:
            response = requests.post(
                url,
                headers=headers,
                data=data,
                proxies=proxy_dict,
                timeout=10,
                verify=False
            )
            response.raise_for_status()
            chat_data = response.json()
            messages = []
            for key, msg_data in chat_data.items():
                if f"RoomMessageTopic#RoomMessageTopic:{broadcaster_uid}" in msg_data:
                    msg = msg_data[f"RoomMessageTopic#RoomMessageTopic:{broadcaster_uid}"]
                    messages.append({
                        "username": msg.get("from_user", {}).get("username", "unknown"),
                        "message": msg.get("message", ""),
                        "timestamp": datetime.now().isoformat()
                    })
            logger.info(f"Fetched {len(messages)} Chaturbate chat messages for {streamer} at {room_url}")
            return messages
        except Exception as e:
            attempts += 1
            logger.warning(f"Attempt {attempts} failed for Chaturbate chat fetch for {streamer} at {room_url}: {e}")
            if attempts < max_attempts:
                time.sleep(1)
    logger.error(f"Failed to fetch Chaturbate chat for {streamer} at {room_url} after {max_attempts} attempts")
    return []

def fetch_stripchat_chat(room_url, streamer):
    """Fetch Stripchat chat messages using proxies"""
    url = f"https://stripchat.com/api/front/v2/models/username/{streamer}/chat"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': f'https://stripchat.com/{streamer}',
        'content-type': 'application/json',
        'front-version': '11.1.89',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Connection': 'keep-alive',
    }
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        proxy_dict = get_random_proxy()
        try:
            response = requests.get(
                url,
                headers=headers,
                proxies=proxy_dict,
                timeout=10,
                verify=False
            )
            response.raise_for_status()
            chat_data = response.json().get("messages", [])
            messages = []
            for msg in chat_data:
                message_type = msg.get("type", "")
                details = msg.get("details", {})
                body = details.get("body", "")
                # Include text messages and tip messages with a non-empty body
                if message_type == "text" or (message_type == "tip" and body):
                    messages.append({
                        "username": msg.get("userData", {}).get("username", "unknown"),
                        "message": body,
                        "timestamp": msg.get("createdAt", datetime.now().isoformat())
                    })
            logger.info(f"Fetched {len(messages)} Stripchat chat messages for {streamer} at {room_url}")
            return messages
        except Exception as e:
            attempts += 1
            logger.warning(f"Attempt {attempts} failed for Stripchat chat fetch for {streamer} at {room_url}: {e}")
            if attempts < max_attempts:
                time.sleep(1)
    logger.error(f"Failed to fetch Stripchat chat for {streamer} at {room_url} after {max_attempts} attempts")
    return []

def fetch_chat_messages(room_url):
    """Fetch chat messages based on platform"""
    logger.debug(f"Fetching chat messages for room_url: {room_url}")
    if not ENABLE_CHAT_MONITORING:
        logger.info(f"Chat monitoring disabled for {room_url}")
        return []
    platform, streamer, broadcaster_uid = get_stream_info(room_url)
    logger.debug(f"Platform: {platform}, Streamer: {streamer}, Broadcaster UID: {broadcaster_uid}")
    try:
        if platform == "chaturbate":
            return fetch_chaturbate_chat(room_url, streamer, broadcaster_uid)
        elif platform == "stripchat":
            return fetch_stripchat_chat(room_url, streamer)
        else:
            logger.warning(f"Unsupported platform {platform} for {room_url}")
            return []
    except Exception as e:
        logger.error(f"Chat fetch error for {room_url}: {e}")
        return []

def process_chat_messages(messages, room_url):
    """Analyze chat messages for keywords and sentiment"""
    if not ENABLE_CHAT_MONITORING:
        logger.info(f"Chat monitoring disabled for {room_url}")
        return []
    keywords = refresh_flagged_keywords()
    if not keywords:
        logger.debug(f"No flagged keywords found for {room_url}")
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
    if detected:
        logger.info(f"Detected {len(detected)} chat issues for {room_url}")
    return detected

def log_chat_detection(detections, room_url):
    """Log each chat detection individually"""
    if not ENABLE_CHAT_MONITORING or not detections:
        return
    platform, streamer, _ = get_stream_info(room_url)
    assignment_id, agent_id = get_stream_assignment(room_url)
    with current_app.app_context():
        for det in detections:
            event_type = "chat_sentiment_detection" if det.get("type") == "sentiment" else "chat_detection"
            details = {
                "detection": det,
                "timestamp": datetime.now().isoformat(),
                "streamer_name": streamer,
                "platform": platform,
                "assigned_agent": agent_id
            }
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
            logger.info(f"Logged and notified individual {event_type} for {room_url}: {det.get('keyword', det.get('sentiment_score'))}")