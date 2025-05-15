# services/notification_service.py
from flask import current_app
from extensions import db
from models import User, DetectionLog, ChatMessage
from utils.notifications import emit_notification, emit_message_update
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import logging

class NotificationService:
    @staticmethod
    def send_user_notification(user, event_type, details, room_url=None, platform=None, streamer=None):
        """Send notifications to a user based on their preferences."""
        if not user.receive_updates:
            logging.info(f"Skipping notifications for {user.username} (receive_updates=False)")
            return

        # In-app notification
        NotificationService.create_in_app_notification(user, event_type, details, room_url, platform, streamer)

        # Email notification
        if user.email:
            NotificationService.send_email_notification(user, event_type, details, platform, streamer)

        # Telegram notification
        if user.telegram_chat_id:
            NotificationService.send_telegram_notification(user, event_type, details, platform, streamer)

    @staticmethod
    def create_in_app_notification(user, event_type, details, room_url=None, platform=None, streamer=None):
        """Create an in-app notification."""
        try:
            notification = DetectionLog(
                event_type=event_type,
                room_url=room_url or details.get('room_url', ''),
                details={
                    **details,
                    'platform': platform or details.get('platform', 'Unknown'),
                    'streamer_name': streamer or details.get('streamer_username', 'Unknown'),
                    'assigned_agent': user.id if user.role == 'agent' else None,
                },
                timestamp=datetime.utcnow(),
                read=False,
                assigned_agent=user.id if user.role == 'agent' else None,
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
                "assigned_agent": user.username if user.role == 'agent' else "Unassigned",
            }
            emit_notification(notification_data)
        except Exception as e:
            logging.error(f"Failed to create in-app notification: {str(e)}")
            db.session.rollback()

    @staticmethod
    def send_email_notification(user, event_type, details, platform, streamer):
        """Send an email notification."""
        try:
            msg = MIMEText(
                f"New {event_type.replace('_', ' ').title()} Alert\n"
                f"Platform: {platform or 'Unknown'}\n"
                f"Streamer: {streamer or 'Unknown'}\n"
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
            message = (
                f"🚨 New {event_type.replace('_', ' ').title()}\n"
                f"Platform: {platform or 'Unknown'}\n"
                f"Streamer: {streamer or 'Unknown'}\n"
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
            'assigned_by': assigner.username if assigner else 'System',
            'notes': notes or '',
            'priority': priority,
        }
        NotificationService.send_user_notification(
            agent, 'stream_assigned', details, stream.room_url, stream.type, stream.streamer_username
        )

        # Also create a system message for the agent
        try:
            sys_msg = ChatMessage(
                sender_id=assigner.id if assigner else None,
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