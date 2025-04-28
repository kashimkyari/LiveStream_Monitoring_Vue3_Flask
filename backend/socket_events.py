# socket_events.py
from flask_socketio import emit, join_room, leave_room
from flask import session, current_app, request
from models import db, User
import datetime
import logging
from sqlalchemy import or_
from models import Assignment, DetectionLog, Stream  # Added missing imports

# Track online users
online_users = {}
connected_sids = {}

def register_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        """Client connected"""
        current_app.logger.info(f"Client connected: {request.sid}")
        
        # Check if user is authenticated and update online status
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                user.online = True
                user.last_active = datetime.datetime.now()
                db.session.commit()
                online_users[user_id] = request.sid
                connected_sids[request.sid] = user_id
                
                # Broadcast online status to all clients
                emit('user_status', {'userId': user_id, 'online': True}, broadcast=True)
                
                # Tell client who is online
                emit('initial_status', {
                    'users': [{'userId': uid, 'online': True} for uid in online_users.keys()]
                })
        else:
            # Anonymous connection
            connected_sids[request.sid] = None
            current_app.logger.info(f"Anonymous connection: {request.sid}")

    @socketio.on('disconnect')
    def handle_disconnect(*args):  # Fixed: Accept variable arguments
        """Client disconnected"""
        sid = request.sid
        current_app.logger.info(f"Client disconnected: {sid}")
        
        # Update user status when disconnected
        user_id = connected_sids.get(sid)
        if user_id and user_id in online_users:
            user = User.query.get(user_id)
            if user:
                user.online = False
                user.last_active = datetime.datetime.now()
                db.session.commit()
                del online_users[user_id]
                
                # Broadcast offline status
                emit('user_status', {'userId': user_id, 'online': False}, broadcast=True)
        
        # Clean up the disconnected SID
        if sid in connected_sids:
            del connected_sids[sid]

    @socketio.on('join')
    def on_join(data):
        """Join a specific room"""
        room = data.get('room')
        if room:
            join_room(room)
            current_app.logger.info(f"Client {request.sid} joined room: {room}")
            emit('room_joined', {'room': room, 'success': True}, room=request.sid)

    @socketio.on('leave')
    def on_leave(data):
        """Leave a specific room"""
        room = data.get('room')
        if room:
            leave_room(room)
            current_app.logger.info(f"Client {request.sid} left room: {room}")
            emit('room_left', {'room': room, 'success': True}, room=request.sid)
            
    # Add any other socket events needed for real-time messaging
    @socketio.on('typing')
    def handle_typing(data):
        """Handle typing indicators"""
        user_id = session.get('user_id')
        if not user_id:
            return
            
        sender = User.query.get(user_id)
        if not sender:
            return
            
        receiver_username = data.get('receiver_username')
        is_typing = data.get('typing', False)
        
        if not receiver_username:
            return
            
        # Look up the receiver
        receiver = User.query.filter_by(username=receiver_username).first()
        if not receiver:
            return
            
        # If receiver is online, send typing indicator
        receiver_sid = online_users.get(receiver.id)
        if receiver_sid:
            emit('typing', {
                'sender_username': sender.username,
                'typing': is_typing
            }, room=receiver_sid)

    @socketio.on_error()
    def handle_error(e):
        """Handle Socket.IO errors"""
        current_app.logger.error(f"Socket.IO error: {str(e)}")
        emit('error', {'message': 'An error occurred with the socket connection'}, room=request.sid)

    # ======= Notification-specific events ========
    @socketio.on('connect', namespace='/notifications')
    def handle_notification_connect():
        """Client connected to notifications namespace"""
        current_app.logger.info(f"Client connected to notifications namespace: {request.sid}")
        
        # Check if user is authenticated
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                # Join user-specific room for targeted notifications
                join_room(f"user_{user_id}", namespace='/notifications')
                current_app.logger.info(f"User {user.username} joined notification room")
                
                # Join role-based room
                role_room = f"role_{user.role}"
                join_room(role_room, namespace='/notifications')
                current_app.logger.info(f"User {user.username} joined {role_room} room")
                
                # If agent, join rooms for each assigned stream
                if user.role == 'agent':
                    for assignment in user.assignments:
                        stream_room = f"stream_{assignment.stream_id}"
                        join_room(stream_room, namespace='/notifications')
                        current_app.logger.info(f"Agent {user.username} joined {stream_room} room")
    
    @socketio.on('disconnect', namespace='/notifications')
    def handle_notification_disconnect(*args):  # Fixed: Accept variable arguments
        """Client disconnected from notifications namespace"""
        current_app.logger.info(f"Client disconnected from notifications namespace: {request.sid}")
        
        # Rooms are automatically left on disconnect
    
    @socketio.on('subscribe_to_stream', namespace='/notifications')
    def handle_stream_subscription(data):
        """Subscribe to notifications for a specific stream"""
        stream_id = data.get('stream_id')
        if not stream_id:
            return
            
        user_id = session.get('user_id')
        if not user_id:
            return
            
        user = User.query.get(user_id)
        if not user:
            return
            
        # Check if agent is assigned to this stream
        if user.role == 'agent':
            assignment = Assignment.query.filter_by(agent_id=user_id, stream_id=stream_id).first()
            if not assignment and not user.role == 'admin':
                emit('error', {'message': 'Not authorized to subscribe to this stream'}, namespace='/notifications')
                return
        
        stream_room = f"stream_{stream_id}"
        join_room(stream_room, namespace='/notifications')
        current_app.logger.info(f"User {user.username} subscribed to {stream_room}")
        emit('subscription_success', {'stream_id': stream_id}, namespace='/notifications')
    
    @socketio.on('unsubscribe_from_stream', namespace='/notifications')
    def handle_stream_unsubscription(data):
        """Unsubscribe from notifications for a specific stream"""
        stream_id = data.get('stream_id')
        if not stream_id:
            return
            
        stream_room = f"stream_{stream_id}"
        leave_room(stream_room, namespace='/notifications')
        current_app.logger.info(f"User left {stream_room}")
        emit('unsubscription_success', {'stream_id': stream_id}, namespace='/notifications')
    
    # Handle missed notifications request
    @socketio.on('get_unread_notifications', namespace='/notifications')
    def handle_unread_notifications_request():
        """Send unread notifications to the client"""
        user_id = session.get('user_id')
        if not user_id:
            return
            
        user = User.query.get(user_id)
        if not user:
            return
            
        try:
            # Query for unread notifications relevant to this user
            if user.role == 'admin':
                # Admins see all unread notifications
                unread_notifications = DetectionLog.query.filter_by(read=False).order_by(DetectionLog.timestamp.desc()).all()
            else:
                # Agents only see notifications for their assigned streams
                assigned_streams = [assignment.stream_id for assignment in user.assignments]
                
                # Get stream URLs for these stream IDs
                stream_urls = [stream.room_url for stream in Stream.query.filter(Stream.id.in_(assigned_streams)).all()]
                
                # Query for notifications with these stream URLs or assigned directly to this agent
                unread_notifications = DetectionLog.query.filter(
                    DetectionLog.read == False,
                    or_(
                        DetectionLog.room_url.in_(stream_urls),
                        # Check if assigned_agent matches in details JSON
                        DetectionLog.details.contains({"assigned_agent": user.username})
                    )
                ).order_by(DetectionLog.timestamp.desc()).all()
            
            # Format notifications for sending
            formatted_notifications = []
            for n in unread_notifications:
                formatted_notifications.append({
                    "id": n.id,
                    "event_type": n.event_type,
                    "timestamp": n.timestamp.isoformat(),
                    "details": n.details,
                    "read": n.read,
                    "room_url": n.room_url,
                    "streamer": n.details.get('streamer_name', 'Unknown'),
                    "platform": n.details.get('platform', 'Unknown'),
                    "assigned_agent": n.details.get('assigned_agent', 'Unassigned')
                })
            
            # Send the unread notifications to the client
            emit('unread_notifications', {'notifications': formatted_notifications}, namespace='/notifications')
            
        except Exception as e:
            current_app.logger.error(f"Error getting unread notifications: {str(e)}")
            emit('error', {'message': 'Error retrieving unread notifications'}, namespace='/notifications')

    # Function that can be used from other parts of the application
    def emit_notification(data):
        """Emit a notification to connected clients from outside a Socket.IO context"""
        try:
            user_id = data.get('user_id')
            if user_id and user_id in online_users:
                socketio.emit('notification', data, room=online_users[user_id])
                return True
            else:
                # Broadcast to all if no specific user
                socketio.emit('notification', data, broadcast=True)
                return True
        except Exception as e:
            current_app.logger.error(f"Error emitting notification: {str(e)}")
            return False
    
    # Make this function available
    socketio.emit_notification = emit_notification