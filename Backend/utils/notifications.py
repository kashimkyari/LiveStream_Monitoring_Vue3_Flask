# utils/notifications.py
from flask_socketio import SocketIO
from flask import current_app

# Initialize Socket.IO without eventlet dependency
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

def init_socketio(app):
    """Initialize socketio with the Flask app"""
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    return socketio

def emit_notification(notification_data):
    """Emit a notification to all connected clients"""
    try:
        socketio.emit('notification', notification_data, namespace='/notifications')
        current_app.logger.info(f"Emitted notification: {notification_data.get('event_type')}")
        
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
        current_app.logger.error(f"Error emitting notification: {str(e)}")
        return False

def emit_notification_update(notification_id, update_type='read'):
    """Emit a notification update (read, deleted, etc.) to all connected clients"""
    try:
        socketio.emit('notification_update', {
            'id': notification_id,
            'type': update_type
        }, namespace='/notifications')
        current_app.logger.info(f"Emitted notification update: {update_type} for {notification_id}")
        return True
    except Exception as e:
        current_app.logger.error(f"Error emitting notification update: {str(e)}")
        return False

def emit_stream_update(stream_data):
    """Emit a stream update to all connected clients"""
    try:
        socketio.emit('stream_update', stream_data)
        current_app.logger.info(f"Emitted stream update for stream ID: {stream_data.get('id')}")
    except Exception as e:
        current_app.logger.error(f"Error emitting stream update: {str(e)}")

def emit_message_update(message_data):
    """Emit a message notification to specific recipients"""
    try:
        receiver_id = message_data.get('receiver_id')
        if receiver_id:
            # Emit to specific room (users subscribe to their own user ID room)
            socketio.emit('new_message', message_data, room=f"user_{receiver_id}")
            current_app.logger.info(f"Emitted message notification to user: {receiver_id}")
        
        # Also emit to sender's room for sent messages confirmation
        sender_id = message_data.get('sender_id')
        if sender_id:
            socketio.emit('message_sent', message_data, room=f"user_{sender_id}")
    except Exception as e:
        current_app.logger.error(f"Error emitting message notification: {str(e)}")

def emit_assignment_update(assignment_data):
    """Emit an assignment update to affected agents"""
    try:
        agent_id = assignment_data.get('agent_id')
        if agent_id:
            socketio.emit('assignment_update', assignment_data, room=f"user_{agent_id}")
            current_app.logger.info(f"Emitted assignment notification to agent: {agent_id}")
    except Exception as e:
        current_app.logger.error(f"Error emitting assignment notification: {str(e)}")

def emit_stream_notification(notification_data, stream_id):
    """Emit a notification to users subscribed to a specific stream"""
    try:
        stream_room = f"stream_{stream_id}"
        socketio.emit('notification', notification_data, room=stream_room, namespace='/notifications')
        current_app.logger.info(f"Emitted notification to stream room: {stream_room}")
        return True
    except Exception as e:
        current_app.logger.error(f"Error emitting stream notification: {str(e)}")
        return False

def emit_role_notification(notification_data, role):
    """Emit a notification to all users with a specific role"""
    try:
        role_room = f"role_{role}"
        socketio.emit('notification', notification_data, room=role_room, namespace='/notifications')
        current_app.logger.info(f"Emitted notification to role room: {role_room}")
        return True
    except Exception as e:
        current_app.logger.error(f"Error emitting role notification: {str(e)}")
        return False

def emit_agent_notification(notification_data, agent_id):
    """Emit a notification to a specific agent"""
    try:
        agent_room = f"user_{agent_id}"
        socketio.emit('notification', notification_data, room=agent_room, namespace='/notifications')
        current_app.logger.info(f"Emitted notification to agent: {agent_id}")
        return True
    except Exception as e:
        current_app.logger.error(f"Error emitting agent notification: {str(e)}")
        return False