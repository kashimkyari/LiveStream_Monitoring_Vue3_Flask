# utils/notifications.py
from flask_socketio import SocketIO
import os
import logging
from models import Stream, User

# Initialize logger
logger = logging.getLogger(__name__)

# Cache for agent usernames
agent_cache = {}

# Module-level SocketIO instance
socketio = None

def init_socketio(app):
    """Initialize SocketIO with proper configuration"""
    global socketio
    try:
        allowed_origins = os.getenv('ALLOWED_ORIGINS', '').split(',') if os.getenv('ALLOWED_ORIGINS') else ['*']
        socketio = SocketIO(
            app,
            async_mode='gevent',
            cors_allowed_origins=allowed_origins,
            logger=True,
            engineio_logger=True
        )
        logger.info("SocketIO initialized in notifications module")
        return socketio
    except Exception as e:
        logger.error(f"Error initializing SocketIO: {str(e)}")
        raise

def get_socketio():
    """Get the module-level socketio instance"""
    global socketio
    if not socketio:
        logger.error("Socket.IO not initialized")
        return None
    return socketio

def emit_notification(notification_data):
    """Emit a notification to all connected clients"""
    socketio = get_socketio()
    if not socketio:
        logger.error("Socket.IO not initialized")
        return False
        
    try:
        socketio.emit('notification', notification_data, namespace='/notifications')
        logger.info(f"Emitted notification: {notification_data.get('event_type', 'unknown')}")
        
        # Also emit to admin users specifically
        emit_role_notification(notification_data, 'admin')
        
        # If notification is for a specific stream, emit to its room
        stream_url = notification_data.get('room_url')
        if stream_url:
            stream = Stream.query.filter_by(room_url=stream_url).first()
            if stream:
                emit_stream_notification(notification_data, stream.id)
                
                # If the notification is assigned to a specific agent
                assigned_agent = notification_data.get('assigned_agent')
                if assigned_agent and assigned_agent != 'Unassigned':
                    agent = User.query.filter_by(username=assigned_agent).first()
                    if agent:
                        emit_agent_notification(notification_data, agent.id)
        
        return True
    except Exception as e:
        logger.error(f"Error emitting notification: {str(e)}")
        return False

def emit_notification_update(notification_id, update_type='read'):
    """Emit a notification update (read, deleted, etc.) to all connected clients"""
    socketio = get_socketio()
    if not socketio:
        logger.error("Socket.IO not initialized")
        return False
        
    try:
        socketio.emit('notification_update', {
            'id': notification_id,
            'type': update_type
        }, namespace='/notifications')
        logger.info(f"Emitted notification update: {update_type} for {notification_id}")
        return True
    except Exception as e:
        logger.error(f"Error emitting notification update: {str(e)}")
        return False

def emit_stream_update(stream_data):
    """Emit a stream update to all connected clients"""
    socketio = get_socketio()
    if not socketio:
        logger.error("Socket.IO not initialized")
        return False
        
    try:
        socketio.emit('stream_update', stream_data)
        logger.info(f"Emitted stream update for stream ID: {stream_data.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Error emitting stream update: {str(e)}")
        return False

def emit_message_update(message_data):
    """Emit a message notification to specific recipients"""
    socketio = get_socketio()
    if not socketio:
        logger.error("Socket.IO not initialized")
        return False
        
    try:
        receiver_id = message_data.get('receiver_id')
        if receiver_id:
            # Emit to specific room (users subscribe to their own user ID room)
            socketio.emit('new_message', message_data, room=f"user_{receiver_id}")
            logger.info(f"Emitted message notification to user: {receiver_id}")
        
        # Also emit to sender's room for sent messages confirmation
        sender_id = message_data.get('sender_id')
        if sender_id:
            socketio.emit('message_sent', message_data, room=f"user_{sender_id}")
        return True
    except Exception as e:
        logger.error(f"Error emitting message notification: {str(e)}")
        return False

def emit_assignment_update(assignment_data):
    """Emit an assignment update to affected agents"""
    socketio = get_socketio()
    if not socketio:
        logger.error("Socket.IO not initialized")
        return False
        
    try:
        agent_id = assignment_data.get('agent_id')
        if agent_id:
            socketio.emit('assignment_update', assignment_data, room=f"user_{agent_id}")
            logger.info(f"Emitted assignment notification to agent: {agent_id}")
        return True
    except Exception as e:
        logger.error(f"Error emitting assignment notification: {str(e)}")
        return False

def emit_stream_notification(notification_data, stream_id):
    """Emit a notification to users subscribed to a specific stream"""
    socketio = get_socketio()
    if not socketio:
        logger.error("Socket.IO not initialized")
        return False
        
    try:
        stream_room = f"stream_{stream_id}"
        socketio.emit('notification', notification_data, room=stream_room, namespace='/notifications')
        logger.info(f"Emitted notification to stream room: {stream_room}")
        return True
    except Exception as e:
        logger.error(f"Error emitting stream notification: {str(e)}")
        return False

def emit_role_notification(notification_data, role):
    """Emit a notification to all users with a specific role"""
    socketio = get_socketio()
    if not socketio:
        logger.error("Socket.IO not initialized")
        return False
        
    try:
        role_room = f"role_{role}"
        socketio.emit('notification', notification_data, room=role_room, namespace='/notifications')
        logger.info(f"Emitted notification to role room: {role_room}")
        return True
    except Exception as e:
        logger.error(f"Error emitting role notification: {str(e)}")
        return False

def emit_agent_notification(notification_data, agent_id):
    """Emit a notification to a specific agent"""
    socketio = get_socketio()
    if not socketio:
        logger.error("Socket.IO not initialized")
        return False
        
    try:
        agent_room = f"user_{agent_id}"
        socketio.emit('notification', notification_data, room=agent_room, namespace='/notifications')
        logger.info(f"Emitted notification to agent: {agent_id}")
        return True
    except Exception as e:
        logger.error(f"Error emitting agent notification: {str(e)}")
        return False