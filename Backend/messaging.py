import os
import datetime
from flask import session, request
from flask_socketio import emit, join_room, disconnect
from models import db, User, ChatMessage, MessageAttachment
from utils.notifications import get_socketio, emit_message_update

# Get the global socketio instance
socketio = get_socketio()
online_users = {}  # {user_id: sid}

def register_messaging_events():
    if not socketio:
        raise RuntimeError("SocketIO not initialized. Call init_socketio() first.")
    
    @socketio.on('connect')
    def handle_connect():
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                user.online = True
                user.last_active = datetime.datetime.now()
                db.session.commit()
                online_users[user_id] = request.sid
                emit('user_status', {'userId': user_id, 'online': True}, broadcast=True)
                
                # Tell client who is online
                emit('initial_status', {
                    'users': [{'userId': uid, 'online': True} for uid in online_users.keys()]
                })

    @socketio.on('disconnect')
    def handle_disconnect():
        user_id = session.get('user_id')
        if user_id and user_id in online_users:
            user = User.query.get(user_id)
            if user:
                user.online = False
                user.last_active = datetime.datetime.now()
                db.session.commit()
                del online_users[user_id]
                emit('user_status', {'userId': user_id, 'online': False}, broadcast=True)

    @socketio.on('user_activity')
    def handle_activity():
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                user.last_active = datetime.datetime.now()
                db.session.commit()

    @socketio.on('send_message')
    def handle_send_message(data):
        """
        Expected data:
        {
            "receiver_username": "<str>",
            "message": "<message text>",
            "attachment": {
                "id": "<int>",
                "url": "<str>",
                "name": "<str>",
                "type": "<str>",
                "size": "<int>"
            }
        }
        """
        sender_id = session.get('user_id')
        if not sender_id:
            emit('error', {'error': 'User not authenticated.'})
            return

        receiver_username = data.get('receiver_username')
        message_text = data.get('message', '')
        attachment = data.get('attachment')

        if not receiver_username:
            emit('error', {'error': 'Missing receiver_username.'})
            return
            
        if not message_text and not attachment:
            emit('error', {'error': 'Message or attachment required.'})
            return

        # Look up the receiver by username
        receiver = User.query.filter_by(username=receiver_username).first()
        if not receiver:
            emit('error', {'error': f'User {receiver_username} not found.'})
            return

        try:
            # Create and save the chat message in the database
            new_message = ChatMessage(
                sender_id=sender_id,
                receiver_id=receiver.id,
                message=message_text,
                timestamp=datetime.datetime.utcnow(),
                read=False,
                is_system=False
            )
            
            # Link attachment if provided
            if attachment and 'id' in attachment:
                attachment_record = MessageAttachment.query.get(attachment['id'])
                if attachment_record and attachment_record.user_id == sender_id:
                    new_message.attachment_id = attachment_record.id
                    
            db.session.add(new_message)
            db.session.commit()

            # Get the serialized message with attachment
            message_data = {
                "id": new_message.id,
                "sender_id": new_message.sender_id,
                "receiver_id": new_message.receiver_id,
                "message": new_message.message,
                "timestamp": new_message.timestamp.isoformat(),
                "is_system": new_message.is_system,
                "read": new_message.read
            }
            
            # Add attachment information if present
            if hasattr(new_message, 'attachment_id') and new_message.attachment_id:
                attachment_record = MessageAttachment.query.get(new_message.attachment_id)
                if attachment_record:
                    message_data["attachment"] = {
                        "id": attachment_record.id,
                        "url": attachment_record.url,
                        "name": attachment_record.filename,
                        "type": attachment_record.mime_type,
                        "size": attachment_record.size
                    }
            
            # Find receiver's socket ID
            receiver_sid = online_users.get(receiver.id)
            
            # If receiver is online, send the message directly
            if receiver_sid:
                emit('receive_message', message_data, room=receiver_sid)
                
            # Also send the message back to the sender to confirm
            emit('receive_message', message_data)
            
            # Emit message notification through regular channels too
            if hasattr(emit_message_update, '__call__'):
                emit_message_update(message_data)
            
        except Exception as e:
            db.session.rollback()
            emit('error', {'error': str(e)})

    @socketio.on('typing')
    def handle_typing(data):
        """
        Expected data:
        {
            "receiver_username": "<str>",
            "typing": <bool>
        }
        """
        sender_id = session.get('user_id')
        if not sender_id:
            return
            
        sender = User.query.get(sender_id)
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
            
        # Find receiver's socket ID
        receiver_sid = online_users.get(receiver.id)
        
        # If receiver is online, send typing indicator
        if receiver_sid:
            emit('typing', {
                'sender_username': sender.username,
                'typing': is_typing
            }, room=receiver_sid)

    # Add this to socket event handlers in messaging.py
    @socketio.on('message_status_update')
    def handle_message_status_update(data):
        """
        Expected data:
        {
            "message_id": "<int>",
            "status": "<str>" (e.g., "read", "delivered")
        }
        """
        user_id = session.get('user_id')
        if not user_id:
            return
            
        message_id = data.get('message_id')
        status = data.get('status')
        
        if not message_id or not status:
            return
            
        try:
            message = ChatMessage.query.get(message_id)
            
            if not message:
                return
                
            # Only allow the receiver to mark messages as read
            if message.receiver_id != user_id:
                return
                
            if status == 'read':
                message.read = True
                db.session.commit()
                
                # Notify the sender if they're online
                if message.sender_id in online_users:
                    emit('message_status_update', {
                        'message_id': message_id,
                        'status': 'read'
                    }, room=online_users[message.sender_id])
        except Exception as e:
            print(f"Error updating message status: {e}")

