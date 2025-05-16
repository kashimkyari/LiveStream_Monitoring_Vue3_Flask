# services/notification_service.py
from flask import current_app
from extensions import db
from models import User, DetectionLog, ChatMessage
from utils.notifications import emit_notification, emit_message_update
from datetime import datetime
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
import logging
import time
import threading

class NotificationService:
    # Rate limiting configuration per channel
    RATE_LIMIT_CONFIG = {
        'in_app': {'max_notifications': 3, 'time_window_seconds': 3600},  # 3 per hour
        'email': {'max_notifications': 2, 'time_window_seconds': 3600},  # 2 per hour
        'telegram': {'max_notifications': 3, 'time_window_seconds': 3600},  # 3 per hour
    }

    # In-memory store for timestamps with thread safety
    _notification_timestamps = defaultdict(lambda: defaultdict(list))
    _lock = threading.Lock()

    @staticmethod
    def _get_user_rate_limit_config(user, channel):
        """Get rate limit configuration for a user and channel, considering role."""
        default_config = NotificationService.RATE_LIMIT_CONFIG[channel]
        # Admins get higher in-app limit
        if user.role == 'admin' and channel == 'in_app':
            return {'max_notifications': 5, 'time_window_seconds': 3600}
        return default_config

    @staticmethod
    def _check_rate_limit(user_id, channel):
        """Check if the user has exceeded the rate limit for a specific channel."""
        try:
            current_time = time.time()
            config = NotificationService._get_user_rate_limit_config(
                User.query.get(user_id), channel
            )
            window_start = current_time - config['time_window_seconds']

            with NotificationService._lock:
                # Filter timestamps within the time window
                NotificationService._notification_timestamps[user_id][channel] = [
                    ts for ts in NotificationService._notification_timestamps[user_id][channel]
                    if ts > window_start
                ]

                # Check if limit is exceeded
                if len(NotificationService._notification_timestamps[user_id][channel]) >= config['max_notifications']:
                    logging.warning(f"Rate limit exceeded for user_id {user_id} on channel {channel}")
                    return False

                # Add new timestamp
                NotificationService._notification_timestamps[user_id][channel].append(current_time)
                return True
        except Exception as e:
            logging.error(f"Rate limit check failed for user_id {user_id}, channel {channel}: {str(e)}")
            # Fallback: Allow notification to avoid blocking
            return True

    @staticmethod
    def _cleanup_timestamps():
        """Remove old timestamps to prevent memory growth."""
        try:
            current_time = time.time()
            with NotificationService._lock:
                for user_id in list(NotificationService._notification_timestamps.keys()):
                    for channel in list(NotificationService._notification_timestamps[user_id].keys()):
                        config = NotificationService._get_user_rate_limit_config(
                            User.query.get(user_id), channel
                        )
                        window_start = current_time - config['time_window_seconds']
                        NotificationService._notification_timestamps[user_id][channel] = [
                            ts for ts in NotificationService._notification_timestamps[user_id][channel]
                            if ts > window_start
                        ]
                        # Remove empty channels/users
                        if not NotificationService._notification_timestamps[user_id][channel]:
                            del NotificationService._notification_timestamps[user_id][channel]
                    if not NotificationService._notification_timestamps[user_id]:
                        del NotificationService._notification_timestamps[user_id]
        except Exception as e:
            logging.error(f"Timestamp cleanup failed: {str(e)}")

    @staticmethod
    def send_user_notification(user, event_type, details, room_url=None, platform=None, streamer=None):
        """Send notifications to a user based on their preferences, with per-channel rate limiting."""
        if not user.receive_updates:
            logging.info(f"Skipping notifications for {user.username} (receive_updates=False)")
            return

        # Clean up timestamps periodically (e.g., every 100 calls)
        if len(NotificationService._notification_timestamps) % 100 == 0:
            NotificationService._cleanup_timestamps()

        channels_sent = []

        # In-app notification
        if NotificationService._check_rate_limit(user.id, 'in_app'):
            NotificationService.create_in_app_notification(user, event_type, details, room_url, platform, streamer)
            channels_sent.append('in_app')

        # Email notification
        if user.email and NotificationService._check_rate_limit(user.id, 'email'):
            NotificationService.send_email_notification(user, event_type, details, platform, streamer)
            channels_sent.append('email')

        # Telegram notification
        if user.telegram_chat_id and NotificationService._check_rate_limit(user.id, 'telegram'):
            NotificationService.send_telegram_notification(user, event_type, details, platform, streamer)
            channels_sent.append('telegram')

        if channels_sent:
            logging.info(f"Sent notifications to {user.username} via {', '.join(channels_sent)} for {event_type}")
        else:
            logging.info(f"No notifications sent to {user.username} for {event_type} due to rate limits")

    @staticmethod
    def create_in_app_notification(user, event_type, details, room_url=None, platform=None, streamer=None):
        """Create an in-app notification."""
        try:
            # Fetch agent username if assigned_agent is an ID
            assigned_agent_username = None
            if user.role == 'agent':
                assigned_agent_username = user.username
            elif 'assigned_agent' in details and details['assigned_agent']:
                agent = User.query.filter_by(id=details['assigned_agent'], role="agent").first()
                assigned_agent_username = agent.username if agent else "Unknown"

            notification = DetectionLog(
                event_type=event_type,
                room_url=room_url or details.get('room_url', ''),
                details={
                    **details,
                    'platform': platform or details.get('platform', 'Unknown'),
                    'streamer_name': streamer or details.get('streamer_username', 'Unknown'),
                    'assigned_agent': assigned_agent_username,  # Use username instead of ID
                },
                timestamp=datetime.utcnow(),
                read=False,
                assigned_agent=user.id if user.role == 'agent' else None,  # Keep ID for DB reference
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
                "assigned_agent": assigned_agent_username or "Unassigned",  # Use username in response
            }
            emit_notification(notification_data)
        except Exception as e:
            logging.error(f"Failed to create in-app notification: {str(e)}")
            db.session.rollback()

    @staticmethod
    def send_email_notification(user, event_type, details, platform, streamer):
        """Send an email notification."""
        try:
            # Fetch agent username if assigned_agent is present
            assigned_agent = details.get('assigned_agent', 'Unassigned')
            if assigned_agent and isinstance(assigned_agent, int):
                agent = User.query.filter_by(id=assigned_agent, role="agent").first()
                assigned_agent = agent.username if agent else "Unknown"

            msg = MIMEText(
                f"New {event_type.replace('_', ' ').title()} Alert\n"
                f"Platform: {platform or 'Unknown'}\n"
                f"Streamer: {streamer or 'Unknown'}\n"
                f"Assigned Agent: {assigned_agent}\n"
                f"Details: {details.get('message', 'No details provided')}\n"
                f"URL: {details.get('room_url', 'No URL provided')}"
            )
            msg['Subject'] = f"[StreamMonitor] {event_type.replace('_', ' ').title()} Notification"
            msg['From'] = current_app.config.get('EMAIL_FROM', 'no-reply@streammonitor.com')
            msg['To'] = user.email

            with smtplib.SMTP(current_app.config.get('SMTP_SERVER', 'smtp.gmail.com'), 587) as server:
                server.starttls()
                server.login(
                    current_app.config.get('SMTP_USERNAME'),
                    current_app.config.get('SMTP_PASSWORD')
                )
                server.send_message(msg)
            logging.info(f"Sent email to {user.email} for {event_type}")
        except Exception as e:
            logging.error(f"Failed to send email to {user.email}: {str(e)}")

    @staticmethod
    def send_telegram_notification(user, event_type, details, platform, streamer):
        """Send a Telegram notification."""
        try:
            from notifications import send_text_message
            # Fetch agent username if assigned_agent is present
            assigned_agent = details.get('assigned_agent', 'Unassigned')
            if assigned_agent and isinstance(assigned_agent, int):
                agent = User.query.filter_by(id=assigned_agent, role="agent").first()
                assigned_agent = agent.username if agent else "Unknown"

            message = (
                f"🚨 New {event_type.replace('_', ' ').title()}\n"
                f"Platform: {platform or 'Unknown'}\n"
                f"Streamer: {streamer or 'Unknown'}\n"
                f"Assigned Agent: {assigned_agent}\n"
                f"URL: {details.get('room_url', 'No URL provided')}\n"
                f"Details: {details.get('message', 'No details provided')}"
            )
            send_text_message(message, user.telegram_chat_id, None)
            logging.info(f"Sent Telegram message to {user.telegram_chat_id} for {event_type}")
        except Exception as e:
            logging.error(f"Failed to send Telegram to {user.telegram_chat_id}: {str(e)}")

    @staticmethod
    def notify_admins(event_type, details, room_url=None, platform=None, streamer=None):
        """Notify all admins with appropriate channels."""
        admins = User.query.filter_by(role='admin', receive_updates=True).all()
        # Ensure assigned_agent is username in details
        if 'assigned_agent' in details and details['assigned_agent']:
            agent = User.query.filter_by(id=details['assigned_agent'], role="agent").first()
            details['assigned_agent'] = agent.username if agent else "Unknown"
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
            'assigned_agent': sys_msg.receiver_id,  # Include agent's username
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