# socket_events.py
from flask_socketio import emit, join_room, leave_room
from flask import session, current_app, request
from models import db, User
import datetime

# Track online users
online_users = {}

def register_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        """Client connected"""
        current_app.logger.info("Client connected")
        
        # Check if user is authenticated and update online status
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                user.online = True
                user.last_active = datetime.datetime.now()
                db.session.commit()
                online_users[user_id] = request.sid
                
                # Broadcast online status to all clients
                emit('user_status', {'userId': user_id, 'online': True}, broadcast=True)
                
                # Tell client who is online
                emit('initial_status', {
                    'users': [{'userId': uid, 'online': True} for uid in online_users.keys()]
                })

    @socketio.on('disconnect')
    def handle_disconnect():
        """Client disconnected"""
        current_app.logger.info("Client disconnected")
        
        # Update user status when disconnected
        user_id = session.get('user_id')
        if user_id and user_id in online_users:
            user = User.query.get(user_id)
            if user:
                user.online = False
                user.last_active = datetime.datetime.now()
                db.session.commit()
                del online_users[user_id]
                
                # Broadcast offline status
                emit('user_status', {'userId': user_id, 'online': False}, broadcast=True)

    @socketio.on('join')
    def on_join(data):
        """Join a specific room"""
        room = data.get('room')
        if room:
            join_room(room)
            current_app.logger.info(f"Client joined room: {room}")
            emit('room_joined', {'room': room}, room=room)

    @socketio.on('leave')
    def on_leave(data):
        """Leave a specific room"""
        room = data.get('room')
        if room:
            leave_room(room)
            current_app.logger.info(f"Client left room: {room}")
            
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