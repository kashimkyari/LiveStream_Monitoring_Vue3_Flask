# routes/notification_routes.py
from flask import Blueprint, request, jsonify, session
from extensions import db
from models import DetectionLog, User, Stream, Assignment, Log, ChatMessage
from utils import login_required
from sqlalchemy import or_
from datetime import datetime
from utils.notifications import emit_notification, emit_notification_update, emit_message_update

notification_bp = Blueprint('notification', __name__)

@notification_bp.route("/api/logs", methods=["GET"])
@login_required(role="admin")
def get_logs():
    try:
        # Retrieve logs from both Log and DetectionLog tables.
        logs1 = Log.query.order_by(Log.timestamp.desc()).limit(100).all()
        logs2 = DetectionLog.query.order_by(DetectionLog.timestamp.desc()).limit(100).all()
        all_logs = logs1 + logs2
        # Sort combined logs by timestamp descending.
        all_logs.sort(key=lambda x: x.timestamp, reverse=True)
        # Limit to 100 most recent entries.
        recent_logs = all_logs[:100]
        return jsonify([{
            "id": log.id,
            "event_type": log.event_type,
            "timestamp": log.timestamp.isoformat(),
            "details": log.details,
            "read": log.read
        } for log in recent_logs])
    except Exception as e:
        return jsonify({"message": "Error fetching dashboard data", "error": str(e)}), 500

# Endpoint for all notifications - accessible to both admins and agents
@notification_bp.route("/api/notifications", methods=["GET"])
@login_required()
def get_all_notifications():
    try:
        user_id = session.get("user_id")
        user_role = session.get("user_role")
        
        # Get all notifications ordered by timestamp
        notifications = DetectionLog.query.order_by(DetectionLog.timestamp.desc()).all()
        
        # If the user is an agent, filter to only show notifications relevant to them
        if user_role == "agent":
            agent = User.query.get(user_id)
            if not agent:
                return jsonify({"error": "Agent not found"}), 404
                
            # Get streams assigned to this agent
            assigned_streams = [assignment.stream_id for assignment in agent.assignments]
            
            # Filter notifications:
            # 1. Include notifications where assigned_agent matches the current agent's username
            # 2. Include notifications related to streams assigned to this agent
            relevant_notifications = []
            
            for notification in notifications:
                # Check if notification is explicitly assigned to this agent
                details = notification.details or {}
                assigned_agent = details.get('assigned_agent')
                
                if assigned_agent and assigned_agent.lower() == agent.username.lower():
                    relevant_notifications.append(notification)
                    continue
                    
                # Check if notification is for a stream assigned to this agent
                stream = Stream.query.filter_by(room_url=notification.room_url).first()
                if stream and stream.id in assigned_streams:
                    relevant_notifications.append(notification)
                    
            notifications = relevant_notifications
            
        return jsonify([{
            "id": n.id,
            "event_type": n.event_type,
            "timestamp": n.timestamp.isoformat(),
            "details": n.details,
            "read": n.read,
            "room_url": n.room_url,
            "streamer": n.details.get('streamer_name', 'Unknown'),
            "platform": n.details.get('platform', 'Unknown'),
            "assigned_agent": n.details.get('assigned_agent', 'Unassigned')
        } for n in notifications]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Create a new notification - Admin only
@notification_bp.route("/api/notifications", methods=["POST"])
@login_required(role="admin")
def create_notification():
    try:
        data = request.get_json()
        
        # Required fields
        if not data.get('event_type') or not data.get('room_url'):
            return jsonify({"error": "Missing required fields: event_type, room_url"}), 400
            
        # Create new notification
        notification = DetectionLog(
            event_type=data.get('event_type'),
            room_url=data.get('room_url'),
            timestamp=datetime.utcnow(),
            details=data.get('details', {}),
            read=data.get('read', False)
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # Prepare notification data for Socket.IO
        notification_data = {
            "id": notification.id,
            "event_type": notification.event_type,
            "timestamp": notification.timestamp.isoformat(),
            "details": notification.details,
            "read": notification.read,
            "room_url": notification.room_url,
            "streamer": notification.details.get('streamer_name', 'Unknown'),
            "platform": notification.details.get('platform', 'Unknown'),
            "assigned_agent": notification.details.get('assigned_agent', 'Unassigned')
        }
        
        # Emit real-time notification
        emit_notification(notification_data)
        
        return jsonify({
            "message": "Notification created successfully",
            "notification": notification_data
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Get a specific notification
@notification_bp.route("/api/notifications/<int:notification_id>", methods=["GET"])
@login_required()
def get_notification(notification_id):
    try:
        user_id = session.get("user_id")
        user_role = session.get("user_role")
        
        notification = DetectionLog.query.get(notification_id)
        if not notification:
            return jsonify({"error": "Notification not found"}), 404
            
        # Check permissions for agents
        if user_role == "agent":
            agent = User.query.get(user_id)
            if not agent:
                return jsonify({"error": "Agent not found"}), 404
                
            # Check if notification is explicitly assigned to this agent
            details = notification.details or {}
            assigned_agent = details.get('assigned_agent')
            
            # Check if notification is for a stream assigned to this agent
            stream = Stream.query.filter_by(room_url=notification.room_url).first()
            assigned_streams = [assignment.stream_id for assignment in agent.assignments]
            
            if not ((assigned_agent and assigned_agent.lower() == agent.username.lower()) or 
                   (stream and stream.id in assigned_streams)):
                return jsonify({"error": "Not authorized to view this notification"}), 403
        
        return jsonify({
            "id": notification.id,
            "event_type": notification.event_type,
            "timestamp": notification.timestamp.isoformat(),
            "details": notification.details,
            "read": notification.read,
            "room_url": notification.room_url,
            "streamer": notification.details.get('streamer_name', 'Unknown'),
            "platform": notification.details.get('platform', 'Unknown'),
            "assigned_agent": notification.details.get('assigned_agent', 'Unassigned')
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update a notification - Admin only
@notification_bp.route("/api/notifications/<int:notification_id>", methods=["PUT"])
@login_required(role="admin")
def update_notification(notification_id):
    try:
        notification = DetectionLog.query.get(notification_id)
        if not notification:
            return jsonify({"error": "Notification not found"}), 404
            
        data = request.get_json()
        
        # Update fields that are provided
        if 'event_type' in data:
            notification.event_type = data['event_type']
            
        if 'details' in data:
            notification.details = data['details']
            
        if 'room_url' in data:
            notification.room_url = data['room_url']
            
        if 'read' in data:
            notification.read = data['read']
            
        db.session.commit()
        
        # Emit update notification
        emit_notification_update(notification.id, 'updated')
        
        return jsonify({
            "message": "Notification updated successfully",
            "notification": {
                "id": notification.id,
                "event_type": notification.event_type,
                "timestamp": notification.timestamp.isoformat(),
                "details": notification.details,
                "read": notification.read,
                "room_url": notification.room_url
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@notification_bp.route("/api/notifications/<int:notification_id>/read", methods=["PUT"])
@login_required()
def mark_notification_read(notification_id):
    try:
        user_id = session.get("user_id")
        user_role = session.get("user_role")
        
        notification = DetectionLog.query.get(notification_id)
        if not notification:
            return jsonify({"message": "Notification not found"}), 404
            
        # If user is an agent, check if they have permission to mark this notification as read
        if user_role == "agent":
            agent = User.query.get(user_id)
            if not agent:
                return jsonify({"error": "Agent not found"}), 404
                
            # Check if notification is explicitly assigned to this agent
            details = notification.details or {}
            assigned_agent = details.get('assigned_agent')
            
            if assigned_agent and assigned_agent.lower() != agent.username.lower():
                # Not directly assigned to this agent, check if it's for a stream they're assigned to
                stream = Stream.query.filter_by(room_url=notification.room_url).first()
                if not stream:
                    return jsonify({"error": "Notification not accessible"}), 403
                    
                assignment = Assignment.query.filter_by(agent_id=user_id, stream_id=stream.id).first()
                if not assignment:
                    return jsonify({"error": "Notification not accessible"}), 403
        
        notification.read = True
        db.session.commit()
        
        # Emit real-time update
        emit_notification_update(notification_id, 'read')
        
        return jsonify({"message": "Notification marked as read"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@notification_bp.route("/api/notifications/read-all", methods=["PUT"])
@login_required()
def mark_all_notifications_read():
    try:
        user_id = session.get("user_id")
        user_role = session.get("user_role")
        
        if user_role == "admin":
            # Admins can mark all notifications as read
            notifications = DetectionLog.query.all()
            for notification in notifications:
                notification.read = True
                # Emit update for each notification
                emit_notification_update(notification.id, 'read')
        else:
            # Agents can only mark notifications related to them as read
            agent = User.query.get(user_id)
            if not agent:
                return jsonify({"error": "Agent not found"}), 404
                
            # Get streams assigned to this agent
            assigned_streams = [assignment.stream_id for assignment in agent.assignments]
            
            # Get all notifications
            notifications = DetectionLog.query.all()
            
            for notification in notifications:
                # Mark as read if:
                # 1. Notification is explicitly assigned to this agent
                # 2. Notification is for a stream assigned to this agent
                details = notification.details or {}
                assigned_agent = details.get('assigned_agent')
                
                if assigned_agent and assigned_agent.lower() == agent.username.lower():
                    notification.read = True
                    emit_notification_update(notification.id, 'read')
                    continue
                    
                # Check if notification is for a stream assigned to this agent
                stream = Stream.query.filter_by(room_url=notification.room_url).first()
                if stream and stream.id in assigned_streams:
                    notification.read = True
                    emit_notification_update(notification.id, 'read')
                    
        db.session.commit()
        return jsonify({"message": "All notifications marked as read"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@notification_bp.route("/api/notifications/<int:notification_id>", methods=["DELETE"])
@login_required(role="admin")  # Only admins can delete notifications
def delete_notification(notification_id):
    try:
        notification = DetectionLog.query.get(notification_id)
        if not notification:
            return jsonify({"message": "Notification not found"}), 404
        db.session.delete(notification)
        db.session.commit()
        
        # Emit delete update
        emit_notification_update(notification_id, 'deleted')
        
        return jsonify({"message": "Notification deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete all notifications - Admin only
@notification_bp.route("/api/notifications/delete-all", methods=["DELETE"])
@login_required(role="admin")
def delete_all_notifications():
    try:
        # Get IDs before deletion
        notification_ids = [n.id for n in DetectionLog.query.all()]
        
        # Delete all notifications
        DetectionLog.query.delete()
        db.session.commit()
        
        # Emit delete updates for each notification
        for notification_id in notification_ids:
            emit_notification_update(notification_id, 'deleted')
        
        return jsonify({"message": "All notifications deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Admin-only endpoint to get notifications that have been forwarded to agents
@notification_bp.route("/api/notifications/forwarded", methods=["GET"])
@login_required(role="admin")
def get_forwarded_notifications():
    try:
        forwarded = DetectionLog.query.filter(
            DetectionLog.details['assigned_agent'].isnot(None)
        ).order_by(DetectionLog.timestamp.desc()).limit(100).all()
        
        return jsonify([{
            'id': n.id,
            'timestamp': n.timestamp.isoformat(),
            'assigned_agent': n.details.get('assigned_agent'),
            'platform': n.details.get('platform'),
            'streamer': n.details.get('streamer_name'),
            'status': 'acknowledged' if n.read else 'pending'
        } for n in forwarded]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Admin-only endpoint to forward a notification to an agent
@notification_bp.route("/api/notifications/<int:notification_id>/forward", methods=["POST"])
@login_required(role="admin")
def forward_notification(notification_id):
    data = request.get_json()
    agent_id = data.get("agent_id")
    
    notification = DetectionLog.query.get(notification_id)
    agent = User.query.filter_by(id=agent_id, role="agent").first()
    
    if not notification or not agent:
        return jsonify({"message": "Invalid notification or agent"}), 404

    # Update the notification details to include the assigned agent
    details = notification.details or {}
    details['assigned_agent'] = agent.username
    notification.details = details
    
    # Save to database
    db.session.commit()
    
    # Emit notification update
    emit_notification_update(notification_id, 'forwarded')
    
    # Additionally, create a system message to notify the agent
    try:
        # Build detailed message content
        message_details = {
            "event_type": notification.event_type,
            "timestamp": notification.timestamp.isoformat(),
            "stream_url": notification.room_url,
            "streamer": notification.details.get('streamer_name', 'Unknown'),
            "platform": notification.details.get('platform', 'Unknown')
        }
    
        # Add type-specific details
        if notification.event_type == 'object_detection':
            message_details.update({
                "detections": notification.details.get('detections', []),
                "annotated_image": notification.details.get('annotated_image')
            })
        elif notification.event_type == 'chat_detection':
            message_details.update({
                "keywords": notification.details.get('keywords', []),
                "messages": notification.details.get('detections', [])
            })
        elif notification.event_type == 'audio_detection':
            message_details.update({
                "keyword": notification.details.get('keyword'),
                "transcript": notification.details.get('transcript')
            })
    
        # Create system message
        sys_msg = ChatMessage(
            sender_id=session['user_id'],
            receiver_id=agent.id,
            message=f"🚨 Forwarded {notification.event_type.replace('_', ' ').title()} Alert",
            details=message_details,
            is_system=True,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(sys_msg)
        db.session.commit()
        
        # Emit message notification to agent
        emit_message_update({
            "id": sys_msg.id,
            "sender_id": sys_msg.sender_id,
            "receiver_id": sys_msg.receiver_id,
            "message": sys_msg.message,
            "timestamp": sys_msg.timestamp.isoformat(),
            "is_system": True,
            "read": False,
            "details": message_details
        })
    except Exception as e:
        # Log the error but continue, as the notification has already been assigned
        print(f"Error creating system message: {str(e)}")
    
    return jsonify({
        "message": "Notification forwarded to agent",
        "agent": agent.username
    }), 200