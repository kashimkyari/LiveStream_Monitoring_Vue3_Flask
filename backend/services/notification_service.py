# services/notification_service.py
import time
from flask import current_app
from extensions import db
from models import User, DetectionLog, ChatMessage, Stream, Assignment
from utils.notifications import emit_notification, emit_message_update
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import logging
import os
from telegram import Bot
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

class NotificationService:
    @staticmethod
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
            query = Assignment.query.filter_by(stream_id=stream.id, status='active')
            
            assignments = query.all()
            
            if not assignments:
                logging.info(f"No active assignments found for stream: {room_url}")
                return None, None
            
            # Select the first active assignment
            assignment = assignments[0]
            agent_id = assignment.agent_id
            # Cache the agent username
            NotificationService.fetch_agent_username(agent_id)
            return assignment.id, agent_id
        except Exception as e:
            logging.error(f"Error fetching assignment for stream {room_url}: {e}")
            return None, None

    @staticmethod
    def fetch_agent_username(agent_id):
        """Fetch a single agent's username and cache it."""
        from notifications import agent_cache
        if agent_id in agent_cache:
            return agent_cache[agent_id]
        try:
            agent = User.query.get(agent_id)
            if agent:
                agent_cache[agent_id] = agent.username or f"Agent {agent_id}"
                return agent_cache[agent_id]
            else:
                logging.warning(f"Agent {agent_id} not found")
                agent_cache[agent_id] = f"Agent {agent_id}"
                return agent_cache[agent_id]
        except Exception as e:
            logging.error(f"Error fetching username for agent {agent_id}: {e}")
            agent_cache[agent_id] = f"Agent {agent_id}"
            return agent_cache[agent_id]

    @staticmethod
    def send_user_notification(user, event_type, details, room_url=None, platform=None, streamer=None, is_image=False, image_data=None):
        """Send notifications to a user based on their preferences."""
        if not user.receive_updates:
            logging.info(f"Skipping notifications for {user.username} (receive_updates=False)")
            return

        channels_sent = []

        # In-app notification
        NotificationService.create_in_app_notification(user, event_type, details, room_url, platform, streamer)
        channels_sent.append('in_app')

        # Email notification
        if user.email:
            NotificationService.send_email_notification(user, event_type, details, platform, streamer)
            channels_sent.append('email')

        # Telegram notification
        if user.telegram_chat_id:
            NotificationService.send_telegram_notification(user, event_type, details, platform, streamer, is_image, image_data)
            channels_sent.append('telegram')

        if channels_sent:
            logging.info(f"Sent notifications to {user.username} via {', '.join(channels_sent)} for {event_type}")
        else:
            logging.info(f"No notifications sent to {user.username} for {event_type}")

    @staticmethod
    def create_in_app_notification(user, event_type, details, room_url=None, platform=None, streamer=None):
        """Create an in-app notification with correct agent assignment."""
        try:
            # Get assignment for the stream
            assignment_id, agent_id = NotificationService.get_stream_assignment(room_url) if room_url else (None, None)
            
            # Determine assigned agent username
            assigned_agent_username = None
            if user.role == 'agent':
                assigned_agent_username = user.username
                agent_id = user.id
            elif agent_id:
                assigned_agent_username = NotificationService.fetch_agent_username(agent_id)
            elif 'assigned_agent' in details and details['assigned_agent']:
                try:
                    agent_id = int(details['assigned_agent'])
                    assigned_agent_username = NotificationService.fetch_agent_username(agent_id)
                except (ValueError, TypeError):
                    assigned_agent_username = details['assigned_agent']  # Assume it's already a username

            # Create notification
            notification = DetectionLog(
                event_type=event_type,
                room_url=room_url or details.get('room_url', ''),
                details={
                    **details,
                    'platform': platform or details.get('platform', 'Unknown'),
                    'streamer_name': streamer or details.get('streamer_username', 'Unknown'),
                    'assigned_agent': assigned_agent_username or 'Unassigned',
                },
                timestamp=datetime.utcnow(),
                read=False,
                assigned_agent=agent_id,
                assignment_id=assignment_id,
                detection_image=details.get('image_data') if details.get('image_data') else None
            )
            db.session.add(notification)
            db.session.commit()

            notification_data = {
                "id": notification.id,
                "event_type": event_type,
                "timestamp": notification.timestamp.isoformat(),
                "details": notification.details,
                "read": notification.read,
                "room_url": notification.room_url,
                "streamer": notification.details.get('streamer_name', 'Unknown'),
                "platform": notification.details.get('platform', 'Unknown'),
                "assigned_agent": assigned_agent_username or 'Unassigned',
            }
            emit_notification(notification_data)
        except Exception as e:
            logging.error(f"Failed to create in-app notification: {str(e)}")
            db.session.rollback()

    @staticmethod
    def send_email_notification(user, event_type, details, platform, streamer):
        """Send an email notification with correct agent username."""
        try:
            # Get assignment for the stream
            room_url = details.get('room_url')
            _, agent_id = NotificationService.get_stream_assignment(room_url) if room_url else (None, None)
            
            # Determine assigned agent username
            assigned_agent = None
            if agent_id:
                assigned_agent = NotificationService.fetch_agent_username(agent_id)
            elif 'assigned_agent' in details:
                try:
                    agent_id = int(details['assigned_agent'])
                    assigned_agent = NotificationService.fetch_agent_username(agent_id)
                except (ValueError, TypeError):
                    assigned_agent = details['assigned_agent']  # Assume it's already a username

            msg = MIMEText(
                f"New {event_type.replace('_', ' ').title()} Alert\n"
                f"Platform: {platform or 'Unknown'}\n"
                f"Streamer: {streamer or 'Unknown'}\n"
                f"Assigned Agent: {assigned_agent or 'Unassigned'}\n"
                f"Details: {details.get('message', 'No details provided')}\n"
                f"URL: {details.get('room_url', 'No URL provided')}"
            )
            msg['Subject'] = f"[StreamMonitor] {event_type.replace('_', ' ').title()} Notification"
            msg['From'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@jetcamstudio.com')
            msg['To'] = user.email

            max_retries = int(os.getenv('MAIL_MAX_RETRIES', 3))
            retry_delay = int(os.getenv('MAIL_RETRY_DELAY', 2))

            for attempt in range(max_retries):
                try:
                    with smtplib.SMTP(os.getenv('MAIL_SERVER', 'smtp.gmail.com'), int(os.getenv('MAIL_PORT', 587))) as server:
                        if os.getenv('MAIL_USE_TLS', 'True').lower() == 'true':
                            server.starttls()
                        server.login(
                            os.getenv('MAIL_USERNAME'),
                            os.getenv('MAIL_PASSWORD')
                        )
                        server.send_message(msg)
                    logging.info(f"Sent email to {user.email} for {event_type}")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logging.warning(f"Email attempt {attempt + 1} failed for {user.email}: {str(e)}. Retrying...")
                        time.sleep(retry_delay)
                    else:
                        logging.error(f"Failed to send email to {user.email} after {max_retries} attempts: {str(e)}")
        except Exception as e:
            logging.error(f"Failed to send email to {user.email}: {str(e)}")

    @staticmethod
    def send_telegram_notification(user, event_type, details, platform, streamer, is_image=False, image_data=None):
        """Send a Telegram notification with correct agent username."""
        try:
            bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
            # Get assignment for the stream
            room_url = details.get('room_url')
            _, agent_id = NotificationService.get_stream_assignment(room_url) if room_url else (None, None)
            
            # Determine assigned agent username
            assigned_agent = None
            if agent_id:
                assigned_agent = NotificationService.fetch_agent_username(agent_id)
            elif 'assigned_agent' in details:
                try:
                    agent_id = int(details['assigned_agent'])
                    assigned_agent = NotificationService.fetch_agent_username(agent_id)
                except (ValueError, TypeError):
                    assigned_agent = details['assigned_agent']  # Assume it's already a username

            message = details.get('message', (
                f"🚨 New {event_type.replace('_', ' ').title()}\n"
                f"Platform: {platform or 'Unknown'}\n"
                f"Streamer: {streamer or 'Unknown'}\n"
                f"Assigned Agent: {assigned_agent or 'Unassigned'}\n"
                f"URL: {details.get('room_url', 'No URL provided')}\n"
                f"Details: {details.get('message', 'No details provided')}"
            ))

            if is_image and image_data:
                photo_file = BytesIO(image_data)
                photo_file.seek(0)
                bot.send_photo(chat_id=user.telegram_chat_id, photo=photo_file, caption=message)
            else:
                bot.send_message(chat_id=user.telegram_chat_id, text=message)
            logging.info(f"Sent Telegram message to {user.telegram_chat_id} for {event_type}")
        except Exception as e:
            logging.error(f"Failed to send Telegram to {user.telegram_chat_id}: {str(e)}")

    @staticmethod
    def notify_admins(event_type, details, room_url=None, platform=None, streamer=None):
        """Notify all admins with appropriate channels."""
        admins = User.query.filter_by(role='admin', receive_updates=True).all()
        # Ensure assigned_agent is username
        room_url = room_url or details.get('room_url')
        _, agent_id = NotificationService.get_stream_assignment(room_url) if room_url else (None, None)
        if agent_id:
            details['assigned_agent'] = NotificationService.fetch_agent_username(agent_id)
        elif 'assigned_agent' in details and details['assigned_agent']:
            try:
                agent_id = int(details['assigned_agent'])
                details['assigned_agent'] = NotificationService.fetch_agent_username(agent_id)
            except (ValueError, TypeError):
                pass  # Assume it's already a username
        for admin in admins:
            NotificationService.send_user_notification(
                admin, event_type, details, room_url, platform, streamer
            )

    @staticmethod
    def notify_assignment(agent, stream, assigner, notes=None, priority='normal'):
        """Notify an agent about a new assignment."""
        details = {
            'message': f"New stream assignment: {stream.streamer_username}",
            'room_url': stream.room_url,
            'streamer_username': stream.streamer_username,
            'platform': stream.type,
            'assigned_by': assigner.username if assigner else 'Admin',
            'assigned_agent': agent.username,
            'notes': notes or '',
            'priority': priority,
        }
        NotificationService.send_user_notification(
            agent, 'stream_assigned', details, stream.room_url, stream.type, stream.streamer_username
        )

        # Also create a system message for the agent
        try:
            sys_msg = ChatMessage(
                sender_id=assigner.id if assigner else 1,
                receiver_id=agent.id,
                message=f"📡 New Stream Assignment: {stream.streamer_username}",
                details=details,
                is_system=True,
                timestamp=datetime.utcnow(),
            )
            db.session.add(sys_msg)
            db.session.commit()

            emit_message_update({
                "id": sys_msg.id,
                "sender_id": sys_msg.sender_id,
                "receiver_id": sys_msg.receiver_id,
                "message": sys_msg.message,
                "timestamp": sys_msg.timestamp.isoformat(),
                "is_system": True,
                "read": False,
                "details": details,
            })
        except Exception as e:
            logging.error(f"Failed to create system message for assignment: {str(e)}")
            db.session.rollback()