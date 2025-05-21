# services/notification_service.py
import asyncio
import time
import requests
import threading
from flask import current_app
from flask_socketio import SocketIO
from extensions import db, scheduler
from models import User, DetectionLog, ChatMessage, Stream, Assignment
from utils.notifications import agent_cache
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import logging
import os
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    socketio = None  # Class attribute for SocketIO
    app = None  # Class attribute for Flask app
    # Cache for recent notifications to prevent spamming
    notification_cache = {}
    notification_cache_lock = threading.Lock()  # Thread-safe lock
    NOTIFICATION_DEBOUNCE = 300  # 5 minutes in seconds
    
    # Higher debounce time specifically for stream status notifications
    STREAM_STATUS_DEBOUNCE = 3600  # 1 hour in seconds

    # Cache for stream statuses to detect changes
    stream_status_cache = {}

    # Scheduler for background tasks
    scheduler = BackgroundScheduler()

    @staticmethod
    def init(app):
        """Initialize NotificationService with Flask app and SocketIO."""
        try:
            NotificationService.app = app
            from utils.notifications import init_socketio
            NotificationService.socketio = init_socketio(app)
            logger.info("NotificationService initialized with Flask app and SocketIO")
        except Exception as e:
            logger.error(f"Failed to initialize NotificationService: {str(e)}")
            raise

    @staticmethod
    def start_scheduler():
        """Start the background scheduler for stream status monitoring."""
        if not NotificationService.scheduler.running:
            NotificationService.scheduler.add_job(
                NotificationService.check_stream_statuses,
                trigger=IntervalTrigger(seconds=60),
                id='stream_status_check',
                replace_existing=True
            )
            NotificationService.scheduler.start()
            logger.info("Background scheduler started for stream status monitoring")
        else:
            logger.info("Scheduler already running")

    @staticmethod
    def check_stream_statuses():
        """Periodically check the status of all streams and trigger notifications."""
        start_time = time.time()
        try:
            if not NotificationService.app:
                logger.error("Flask app not initialized in NotificationService")
                return
            with NotificationService.app.app_context():
                streams = Stream.query.all()
                logger.debug(f"Checking {len(streams)} streams")
                for stream in streams:
                    new_status = NotificationService.get_stream_status(stream)
                    old_status = NotificationService.stream_status_cache.get(stream.id, stream.status)
                    
                    if new_status != old_status:
                        logger.info(f"Stream {stream.streamer_username} status changed from {old_status} to {new_status}")
                        stream.status = new_status
                        stream.is_monitored = new_status == 'monitoring'
                        db.session.commit()
                        
                        NotificationService.stream_status_cache[stream.id] = new_status
                        NotificationService.notify_stream_status_change(stream, old_status, new_status)
                logger.debug(f"Stream status check completed in {time.time() - start_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Error checking stream statuses: {str(e)}")
            try:
                with NotificationService.app.app_context():
                    db.session.rollback()
            except Exception as rollback_e:
                logger.error(f"Failed to rollback session: {str(rollback_e)}")
        finally:
            elapsed_time = time.time() - start_time
            if elapsed_time > 60:
                logger.warning(f"Stream status check took {elapsed_time:.2f} seconds, exceeding interval")

    @staticmethod
    def get_stream_status(stream):
        """Check the live status of a stream by querying its m3u8 URL."""
        try:
            if stream.type.lower() == 'chaturbate' and stream.chaturbate_m3u8_url:
                url = stream.chaturbate_m3u8_url
            elif stream.type.lower() == 'stripchat' and stream.stripchat_m3u8_url:
                url = stream.stripchat_m3u8_url
            else:
                url = stream.room_url

            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                return 'online' if not stream.is_monitored else 'monitoring'
            else:
                return 'offline'
        except requests.RequestException as e:
            logger.warning(f"Failed to check status for stream {stream.streamer_username}: {str(e)}")
            return 'offline'

    @staticmethod
    def get_stream_assignment(room_url):
        """Get assignment info for a stream, ensuring correct agent_id."""
        try:
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
                logger.warning(f"No stream found for URL: {room_url}")
                return None, None
            
            query = Assignment.query.filter_by(stream_id=stream.id, status='active')
            assignments = query.all()
            
            if not assignments:
                logger.info(f"No active assignments found for stream: {room_url}")
                return None, None
            
            assignment = assignments[0]
            agent_id = assignment.agent_id
            NotificationService.fetch_agent_username(agent_id)
            return assignment.id, agent_id
        except Exception as e:
            logger.error(f"Error fetching assignment for stream {room_url}: {e}")
            return None, None

    @staticmethod
    def fetch_agent_username(agent_id):
        """Fetch a single agent's username and cache it."""
        if agent_id in agent_cache:
            return agent_cache[agent_id]
        try:
            agent = User.query.get(agent_id)
            if agent:
                username = agent.username or f"Agent {agent_id}"
                agent_cache[agent_id] = username
                logger.debug(f"Cached username for agent {agent_id}: {username}")
                return username
            else:
                logger.warning(f"Agent {agent_id} not found")
                agent_cache[agent_id] = f"Agent {agent_id}"
                return agent_cache[agent_id]
        except Exception as e:
            logger.error(f"Error fetching username for agent {agent_id}: {e}")
            agent_cache[agent_id] = f"Agent {agent_id}"
            return agent_cache[agent_id]

    @staticmethod
    def should_send_notification(user_id, event_type, room_url):
        """Check if a notification should be sent based on recent notifications."""
        cache_key = f"{user_id}_{event_type}_{room_url}"
        with NotificationService.notification_cache_lock:  # Thread-safe access
            last_notification = NotificationService.notification_cache.get(cache_key)
            current_time = datetime.utcnow()
            
            # Use longer debounce period for stream status notifications
            debounce_period = (NotificationService.STREAM_STATUS_DEBOUNCE 
                              if event_type == 'stream_status_update' 
                              else NotificationService.NOTIFICATION_DEBOUNCE)
            
            if last_notification and (current_time - last_notification).total_seconds() < debounce_period:
                logger.info(f"Skipping notification for {cache_key} due to debounce ({debounce_period}s)")
                return False
            NotificationService.notification_cache[cache_key] = current_time
            return True

    @staticmethod
    async def send_telegram_notification(user, event_type, details, platform, streamer, is_image=False, image_data=None):
        """Send a Telegram notification with retry logic."""
        try:
            # Skip stream status notifications for Telegram
            if event_type == 'stream_status_update' and not user.role == 'admin':
                logger.info(f"Skipping Telegram notification for stream status update to {user.username}")
                return
                
            telegram_token = os.getenv('TELEGRAM_TOKEN')
            if not telegram_token:
                logger.error("Telegram token not set in environment variables")
                return

            if not user.telegram_chat_id:
                logger.error(f"No valid Telegram chat ID for user {user.username}")
                return

            # Initialize Telegram bot with async client
            bot = Bot(token=telegram_token)

            # Determine assigned agent username
            room_url = details.get('room_url')
            _, agent_id = NotificationService.get_stream_assignment(room_url) if room_url else (None, None)
            assigned_agent = None
            if agent_id:
                assigned_agent = NotificationService.fetch_agent_username(agent_id)
            elif 'assigned_agent' in details:
                try:
                    agent_id = int(details['assigned_agent'])
                    assigned_agent = NotificationService.fetch_agent_username(agent_id)
                except (ValueError, TypeError):
                    assigned_agent = details['assigned_agent']

            message = details.get('message', (
                f"🚨 New {event_type.replace('_', ' ').title()}\n"
                f"Platform: {platform or 'Unknown'}\n"
                f"Streamer: {streamer or 'Unknown'}\n"
                f"Assigned Agent: {assigned_agent or 'Unassigned'}\n"
                f"URL: {details.get('room_url', 'No URL provided')}\n"
                f"Details: {details.get('message', 'No details provided')}"
            ))

            max_retries = int(os.getenv('TELEGRAM_MAX_RETRIES', 3))
            retry_delay = int(os.getenv('TELEGRAM_RETRY_DELAY', 2))

            for attempt in range(max_retries):
                try:
                    if is_image and image_data:
                        if not isinstance(image_data, bytes) or len(image_data) == 0:
                            logger.warning(f"Invalid image data for Telegram notification to {user.username}")
                            await bot.send_message(chat_id=user.telegram_chat_id, text=message)
                        else:
                            from io import BytesIO
                            photo_file = BytesIO(image_data)
                            photo_file.seek(0)
                            await bot.send_photo(chat_id=user.telegram_chat_id, photo=photo_file, caption=message)
                    else:
                        await bot.send_message(chat_id=user.telegram_chat_id, text=message)
                    logger.info(f"Sent Telegram message to {user.telegram_chat_id} for {event_type}")
                    break
                except TelegramError as te:
                    if attempt < max_retries - 1:
                        logger.warning(f"Telegram attempt {attempt + 1} failed for {user.telegram_chat_id}: {str(te)}. Retrying...")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"Failed to send Telegram to {user.telegram_chat_id} after {max_retries} attempts: {str(te)}")
                        if "chat not found" in str(te).lower():
                            logger.error(f"Invalid chat ID {user.telegram_chat_id} for user {user.username}")
                        elif "blocked by user" in str(te).lower():
                            logger.error(f"Bot blocked by user {user.username} (chat_id: {user.telegram_chat_id})")
                        elif "timeout" in str(te).lower():
                            logger.error(f"Timeout error sending Telegram message to {user.telegram_chat_id}")
                        else:
                            logger.error(f"Unexpected Telegram error: {str(te)}")
                except Exception as e:
                    logger.error(f"Unexpected error sending Telegram to {user.telegram_chat_id}: {str(e)}")
                    break
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot for {user.telegram_chat_id}: {str(e)}")

    @staticmethod
    def send_user_notification(user, event_type, details, room_url=None, platform=None, streamer=None, is_image=False, image_data=None):
        """Send notifications to a user based on their preferences."""
        if not user.receive_updates:
            logger.info(f"Skipping notifications for {user.username} (receive_updates=False)")
            return

        # Special handling for stream status updates
        if event_type == 'stream_status_update':
            # For non-admin users, only create in-app notifications (no email/telegram)
            if user.role != 'admin':
                # Check if notification should be sent (uses longer debounce period)
                if NotificationService.should_send_notification(user.id, event_type, room_url or details.get('room_url', '')):
                    NotificationService.create_in_app_notification(user, event_type, details, room_url, platform, streamer)
                    logger.info(f"Sent in-app notification only for stream status update to {user.username}")
                return
        
        # Regular notification flow for other event types and for admins
        if not NotificationService.should_send_notification(user.id, event_type, room_url or details.get('room_url', '')):
            return

        channels_sent = []

        # In-app notification
        NotificationService.create_in_app_notification(user, event_type, details, room_url, platform, streamer)
        channels_sent.append('in_app')

        # Email notification - skip for stream status updates for non-admins
        if user.email and (event_type != 'stream_status_update' or user.role == 'admin'):
            NotificationService.send_email_notification(user, event_type, details, platform, streamer)
            channels_sent.append('email')

        # Telegram notification - skip for stream status updates for non-admins
        if user.telegram_chat_id and (event_type != 'stream_status_update' or user.role == 'admin'):
            asyncio.run(NotificationService.send_telegram_notification(user, event_type, details, platform, streamer, is_image, image_data))
            channels_sent.append('telegram')

        if channels_sent:
            logger.info(f"Sent notifications to {user.username} via {', '.join(channels_sent)} for {event_type}")
        else:
            logger.info(f"No notifications sent to {user.username} for {event_type}")

    @staticmethod
    def create_in_app_notification(user, event_type, details, room_url=None, platform=None, streamer=None):
        """Create an in-app notification with correct agent assignment."""
        from utils.notifications import emit_notification
        try:
            assignment_id, agent_id = NotificationService.get_stream_assignment(room_url) if room_url else (None, None)
            
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
                    assigned_agent_username = details['assigned_agent']

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
            logger.info(f"Emitted in-app notification for {event_type} to user {user.username}")
        except Exception as e:
            logger.error(f"Failed to create in-app notification: {str(e)}")
            db.session.rollback()

    @staticmethod
    def send_email_notification(user, event_type, details, platform, streamer):
        """Send an email notification with correct agent username."""
        try:
            # Skip email notifications for stream status updates to non-admin users
            if event_type == 'stream_status_update' and user.role != 'admin':
                logger.info(f"Skipping email notification for stream status update to {user.username}")
                return
                
            room_url = details.get('room_url')
            _, agent_id = NotificationService.get_stream_assignment(room_url) if room_url else (None, None)
            
            assigned_agent = None
            if agent_id:
                assigned_agent = NotificationService.fetch_agent_username(agent_id)
            elif 'assigned_agent' in details:
                try:
                    agent_id = int(details['assigned_agent'])
                    assigned_agent = NotificationService.fetch_agent_username(agent_id)
                except (ValueError, TypeError):
                    assigned_agent = details['assigned_agent']

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
                    logger.info(f"Sent email to {user.email} for {event_type}")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Email attempt {attempt + 1} failed for {user.email}: {str(e)}. Retrying...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Failed to send email to {user.email} after {max_retries} attempts: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {str(e)}")

    @staticmethod
    def notify_admins(event_type, details, room_url=None, platform=None, streamer=None):
        """Notify all admins with appropriate channels."""
        admins = User.query.filter_by(role='admin', receive_updates=True).all()
        room_url = room_url or details.get('room_url')
        _, agent_id = NotificationService.get_stream_assignment(room_url) if room_url else (None, None)
        if agent_id:
            details['assigned_agent'] = NotificationService.fetch_agent_username(agent_id)
        elif 'assigned_agent' in details and details['assigned_agent']:
            try:
                agent_id = int(details['assigned_agent'])
                details['assigned_agent'] = NotificationService.fetch_agent_username(agent_id)
            except (ValueError, TypeError):
                pass
        for admin in admins:
            NotificationService.send_user_notification(
                admin, event_type, details, room_url, platform, streamer
            )

    @staticmethod
    def notify_assignment(agent, stream, assigner, notes=None, priority='normal'):
        """Notify an agent about a new assignment."""
        from utils.notifications import emit_message_update
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

        try:
            sys_msg = ChatMessage(
                sender_id=assigner.id if assigner else 1,
                receiver_id=agent.id,
                message=f"📡 New Stream Assignment: {stream.streamer_username}",
                details=details,
                is_system=True,
                timestamp=datetime.utcnow()
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
                "details": details
            })
            logger.info(f"Emitted assignment message for {stream.streamer_username} to agent {agent.username}")
        except Exception as e:
            logger.error(f"Failed to create assignment notification message: {str(e)}")
            db.session.rollback()

    @staticmethod
    def notify_unassignment(agent, stream, assigner):
        """Notify an agent about an unassignment."""
        from utils.notifications import emit_message_update
        details = {
            'message': f"Stream unassigned: {stream.streamer_username}",
            'room_url': stream.room_url,
            'streamer_username': stream.streamer_username,
            'platform': stream.type,
            'unassigned_by': assigner.username if assigner else 'Admin',
            'assigned_agent': agent.username
        }
        NotificationService.send_user_notification(
            agent, 'stream_unassigned', details, stream.room_url, stream.type, stream.streamer_username
        )

        try:
            sys_msg = ChatMessage(
                sender_id=assigner.id if assigner else 1,
                receiver_id=agent.id,
                message=f"📴 Stream Unassigned: {stream.streamer_username}",
                details=details,
                is_system=True,
                timestamp=datetime.utcnow()
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
                "details": details
            })
            logger.info(f"Emitted unassignment message for {stream.streamer_username} to agent {agent.username}")
        except Exception as e:
            logger.error(f"Failed to create unassignment notification message: {str(e)}")
            db.session.rollback()

    @staticmethod
    def notify_stream_status_change(stream, old_status, new_status):
        """Notify relevant users about a stream status change."""
        from utils.notifications import emit_notification
        try:
            # Skip notifications for minor status changes
            if (old_status == 'online' and new_status == 'monitoring') or (old_status == 'monitoring' and new_status == 'online'):
                logger.info(f"Skipping notification for minor status change from {old_status} to {new_status} for {stream.streamer_username}")
                # Still update the database
                notification = DetectionLog(
                    event_type='stream_status_update',
                    room_url=stream.room_url,
                    details={
                        'message': f"Stream status changed from {old_status} to {new_status}",
                        'room_url': stream.room_url,
                        'streamer_username': stream.streamer_username,
                        'platform': stream.type,
                        'status': new_status
                    },
                    timestamp=datetime.utcnow(),
                    read=True,  # Mark as read since we're not notifying anyone
                )
                db.session.add(notification)
                db.session.commit()
                return
                
            details = {
                'message': f"Stream status changed from {old_status} to {new_status}",
                'room_url': stream.room_url,
                'streamer_username': stream.streamer_username,
                'platform': stream.type,
                'status': new_status
            }
            assignment_id, agent_id = NotificationService.get_stream_assignment(stream.room_url)
            if agent_id:
                agent = User.query.get(agent_id)
                if agent and agent.receive_updates:
                    details['assigned_agent'] = agent.username
                    NotificationService.send_user_notification(
                        agent, 'stream_status_update', details, stream.room_url, stream.type, stream.streamer_username
                    )
            
            # Only notify admins about offline->online and online->offline transitions
            if (old_status == 'offline' and new_status in ['online', 'monitoring']) or \
               (old_status in ['online', 'monitoring'] and new_status == 'offline'):
                NotificationService.notify_admins('stream_status_update', details, stream.room_url, stream.type, stream.streamer_username)
            
            # Create a DetectionLog entry for the status change
            notification = DetectionLog(
                event_type='stream_status_update',
                room_url=stream.room_url,
                details=details,
                timestamp=datetime.utcnow(),
                read=False,
                assigned_agent=agent_id,
                assignment_id=assignment_id
            )
            db.session.add(notification)
            db.session.commit()

            notification_data = {
                "id": notification.id,
                "event_type": 'stream_status_update',
                "timestamp": notification.timestamp.isoformat(),
                "details": notification.details,
                "read": notification.read,
                "room_url": notification.room_url,
                "streamer": notification.details.get('streamer_username', 'Unknown'),
                "platform": notification.details.get('platform', 'Unknown'),
                "assigned_agent": details.get('assigned_agent', 'Unassigned')
            }
            emit_notification(notification_data)
            logger.info(f"Emitted stream status update for {stream.streamer_username}: {new_status}")
        except Exception as e:
            logger.error(f"Failed to notify stream status change for {stream.streamer_username}: {str(e)}")
            db.session.rollback()

    @classmethod
    def schedule_status_check(cls):
        try:
            if not scheduler.running:
                scheduler.start()
            
            # Remove existing job if it exists
            scheduler.remove_job('check_stream_statuses', jobstore='default')
            
            # Add new job with error handling
            scheduler.add_job(
                cls.check_stream_statuses,
                'interval',
                minutes=1,
                id='check_stream_statuses',
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
        except RuntimeError as e:
            if "cannot schedule new futures after shutdown" in str(e):
                logging.warning("Scheduler was shut down, attempting restart...")
                scheduler.start()
                cls.schedule_status_check()  # Retry scheduling
            else:
                raise