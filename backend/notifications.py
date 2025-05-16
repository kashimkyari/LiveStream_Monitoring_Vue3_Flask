import os
import json
import logging
import base64
from flask import current_app
from models import Log, User, Stream, Assignment
from extensions import db
from telegram import Bot, InputFile
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import asyncio
from io import BytesIO
from sqlalchemy.orm import joinedload

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
executor = ThreadPoolExecutor(max_workers=5)  # Adjust max_workers as needed

# Agent cache for usernames
agent_cache = {}
all_agents_fetched = False

def fetch_all_agents():
    """Fetch all agents and cache their usernames."""
    global all_agents_fetched
    if all_agents_fetched:
        return
    try:
        agents = User.query.filter_by(role='agent').all()
        for agent in agents:
            agent_cache[agent.id] = agent.username or f"Agent {agent.id}"
        all_agents_fetched = True
        logging.info("All agent usernames cached successfully.")
    except Exception as e:
        logging.error(f"Error fetching all agents: {e}")

def fetch_agent_username(agent_id):
    """Fetch a single agent's username and cache it."""
    if agent_id in agent_cache:
        return agent_cache[agent_id]
    try:
        agent = User.query.get(agent_id)
        if agent:
            agent_cache[agent_id] = agent.username or f"Agent {agent.id}"
            logging.info(f"Cached username for agent {agent_id}: {agent_cache[agent_id]}")
            return agent_cache[agent_id]
        else:
            logging.warning(f"Agent {agent_id} not found")
            agent_cache[agent_id] = f"Agent {agent_id}"
            return agent_cache[agent_id]
    except Exception as e:
        logging.error(f"Error fetching username for agent {agent_id}: {e}")
        agent_cache[agent_id] = f"Agent {agent_id}"
        return agent_cache[agent_id]

def get_bot(token=None):
    """Return a Telegram Bot instance."""
    if token is None:
        token = TELEGRAM_TOKEN
    return Bot(token=token)

async def send_text_message_async(msg, chat_id, token=None):
    """Send a text message asynchronously."""
    try:
        bot = get_bot(token)
        await bot.send_message(chat_id=chat_id, text=msg)
        logging.info(f"Telegram text message sent to chat_id {chat_id}.")
        return True
    except Exception as e:
        logging.error(f"Failed to send Telegram message to chat_id {chat_id}: {e}")
        return False

async def send_telegram_image_async(photo_file, caption, chat_id, token=None):
    """
    Send an image message asynchronously.
    photo_file should be a file-like object (e.g. BytesIO).
    """
    try:
        bot = get_bot(token)
        await bot.send_photo(chat_id=chat_id, photo=photo_file, caption=caption)
        logging.info(f"Telegram image sent to chat_id {chat_id}.")
        return True
    except Exception as e:
        logging.error(f"Failed to send Telegram image to chat_id {chat_id}: {e}")
        return False

def send_text_message(msg, chat_id, token=None):
    """Wrapper to run the async function in a synchronous context."""
    return asyncio.run(send_text_message_async(msg, chat_id, token))

def send_telegram_image(photo_file, caption, chat_id, token=None):
    """Wrapper to run the async function in a synchronous context."""
    return asyncio.run(send_telegram_image_async(photo_file, caption, chat_id, token))

def get_stream_assignment(room_url):
    """Get assignment info for a stream, ensuring correct agent_id."""
    try:
        # Find the stream by room_url or M3U8 URL
        stream = Stream.query.filter_by(room_url=room_url).first()
        if not stream:
            from models import ChaturbateStream, StripchatStream
            cb_stream = ChaturbateStream.query.filter_by(chaturbate_m3u8_url=room_url).first()
            if cb_stream:
                stream = Stream.query.get(cb_stream.id)
            else:
                sc_stream = StripchatStream.query.filter_by(stripchat_m3u8_url=room_url).first()
                if sc_stream:
                    stream = Stream.query.get(sc_stream.id)
        
        if not stream:
            logging.warning(f"No stream found for URL: {room_url}")
            return None, None
        
        # Query assignments for this stream
        query = Assignment.query.options(
            joinedload(Assignment.agent),
            joinedload(Assignment.stream)
        ).filter_by(stream_id=stream.id, status='active')
        
        assignments = query.all()
        
        if not assignments:
            logging.info(f"No active assignments found for stream: {room_url}")
            return None, None
        
        # Select the first active assignment
        assignment = assignments[0]
        agent_id = assignment.agent_id
        fetch_agent_username(agent_id)
        return assignment.id, agent_id
    except Exception as e:
        logging.error(f"Error fetching assignment for stream {room_url}: {e}")
        return None, None

def send_notifications(log_entry, detections=None, platform_name=None, streamer_name=None):
    """
    Sends notifications based on the log_entry from the unified detection API.
    For object detection events, if a stored annotated image is available, it is sent as an image.
    For chat detection events, a Telegram text message is sent with details about the flagged chat message.
    Notifications are sent to users with receive_updates=True and a valid telegram_chat_id,
    prioritizing assigned agents if available.
    """
    try:
        from config import create_app
        app = create_app()
        
        with app.app_context():
            details = log_entry.details or {}
            platform = platform_name if platform_name is not None else details.get('platform', 'Unknown Platform')
            streamer = streamer_name if streamer_name is not None else details.get('streamer_name', 'Unknown Streamer')

            # Get assignment for the stream
            assignment_id, agent_id = get_stream_assignment(log_entry.room_url) if log_entry.room_url else (None, None)
            
            # Determine recipients: prioritize assigned agent, then users with receive_updates=True
            recipients = []
            if agent_id:
                agent = User.query.get(agent_id)
                if agent and agent.telegram_chat_id and agent.receive_updates:
                    recipients.append(agent)
            else:
                # Fallback to all users with telegram_chat_id and receive_updates=True
                recipients = User.query.filter(
                    User.telegram_chat_id.isnot(None),
                    User.receive_updates == True
                ).all()

            if not recipients:
                logging.warning("No eligible Telegram recipients found; skipping notification.")
                return

            # For object detection
            detections_list = detections or details.get('detections') or []
            confidence = None
            if detections_list and isinstance(detections_list, list):
                confidence = detections_list[0].get('confidence')
            conf_str = f"{(confidence * 100):.1f}%" if isinstance(confidence, (int, float)) else "N/A"

            if log_entry.event_type == 'object_detection':
                detected_objects = ", ".join([d["class"] for d in detections_list]) if detections_list else "No details"
                message = (
                    f"🚨 **Object Detection Alert**\n"
                    f"🎥 Platform: {platform}\n"
                    f"📡 Streamer: {streamer}\n"
                    f"📌 Objects Detected: {detected_objects}\n"
                    f"🔍 Confidence: {conf_str}\n"
                    f"👤 Assigned Agent: {fetch_agent_username(agent_id) if agent_id else 'Unassigned'}"
                )
                if log_entry.detection_image:
                    for recipient in recipients:
                        photo_file = BytesIO(log_entry.detection_image)
                        photo_file.seek(0)
                        executor.submit(send_telegram_image, photo_file, message, recipient.telegram_chat_id, None)
                else:
                    for recipient in recipients:
                        executor.submit(send_text_message, message, recipient.telegram_chat_id, None)

            elif log_entry.event_type == 'audio_detection':
                keyword = details.get('keyword', 'N/A')
                transcript = details.get('transcript', 'No transcript available.')
                message = (
                    f"🔊 **Audio Detection Alert**\n"
                    f"🎥 Platform: {platform}\n"
                    f"📡 Streamer: {streamer}\n"
                    f"🔑 Keyword: {keyword}\n"
                    f"📝 Transcript: {transcript[:300]}...\n"
                    f"👤 Assigned Agent: {fetch_agent_username(agent_id) if agent_id else 'Unassigned'}"
                )
                for recipient in recipients:
                    executor.submit(send_text_message, message, recipient.telegram_chat_id, None)

            elif log_entry.event_type == 'chat_detection':
                detections = details.get('detections', [{}])
                first_detection = detections[0] if detections else {}
                message = (
                    f"💬 **Chat Detection Alert**\n"
                    f"🎥 Platform: {platform}\n"
                    f"📡 Streamer: {streamer}\n"
                    f"👤 Sender: {first_detection.get('sender', 'Unknown')}\n"
                    f"🔍 Keywords: {', '.join(first_detection.get('keywords', []))}\n"
                    f"📝 Message: {first_detection.get('message', '')[:300]}...\n"
                    f"👤 Assigned Agent: {fetch_agent_username(agent_id) if agent_id else 'Unassigned'}"
                )
                for recipient in recipients:
                    executor.submit(send_text_message, message, recipient.telegram_chat_id, None)

            elif log_entry.event_type == 'video_notification':
                msg_detail = details.get('message', 'No additional details.')
                message = (
                    f"🎥 **Video Notification**\n"
                    f"🎥 Platform: {platform}\n"
                    f"📡 Streamer: {streamer}\n"
                    f"📝 Message: {msg_detail}\n"
                    f"👤 Assigned Agent: {fetch_agent_username(agent_id) if agent_id else 'Unassigned'}"
                )
                for recipient in recipients:
                    executor.submit(send_text_message, message, recipient.telegram_chat_id, None)

            else:
                message = (
                    f"🔔 **{log_entry.event_type.replace('_', ' ').title()}**\n"
                    f"🎥 Platform: {platform}\n"
                    f"📡 Streamer: {streamer}\n"
                    f"📌 Details: {json.dumps(details, indent=2)[:500]}...\n"
                    f"👤 Assigned Agent: {fetch_agent_username(agent_id) if agent_id else 'Unassigned'}"
                )
                for recipient in recipients:
                    executor.submit(send_text_message, message, recipient.telegram_chat_id, None)
    except Exception as e:
        logging.error(f"Notification error: {str(e)}", exc_info=True)