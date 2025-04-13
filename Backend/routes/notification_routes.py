from flask import Blueprint, request, jsonify

from extensions import db
from models import DetectionLog
from utils import login_required

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
        app.logger.error("Error in /api/logs: %s", e)
        return jsonify({"message": "Error fetching dashboard data", "error": str(e)}), 500


# Add these endpoints for notifications
@notification_bp.route("/api/notifications", methods=["GET"])
@login_required()
def get_all_notifications():
    try:
        notifications = DetectionLog.query.order_by(DetectionLog.timestamp.desc()).all()
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

@notification_bp.route("/api/notifications/<int:notification_id>/read", methods=["PUT"])
@login_required()
def mark_notification_read(notification_id):
    try:
        notification = DetectionLog.query.get(notification_id)
        if not notification:
            return jsonify({"message": "Notification not found"}), 404
        notification.read = True
        db.session.commit()
        return jsonify({"message": "Notification marked as read"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@notification_bp.route("/api/notifications/<int:notification_id>", methods=["DELETE"])
@login_required(role="admin")
def delete_notification(notification_id):
    try:
        notification = DetectionLog.query.get(notification_id)
        if not notification:
            return jsonify({"message": "Notification not found"}), 404
        db.session.delete(notification)
        db.session.commit()
        return jsonify({"message": "Notification deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@notification_bp.route("/api/notifications/read-all", methods=["PUT"])
@login_required()
def mark_all_notifications_read():
    try:
        DetectionLog.query.update({"read": True})
        db.session.commit()
        return jsonify({"message": "All notifications marked as read"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Add to notification endpoints section
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


# Update existing forward endpoint
# routes.py
@notification_bp.route("/api/notifications/<int:notification_id>/forward", methods=["POST"])
@login_required(role="admin")
def forward_notification(notification_id):
    data = request.get_json()
    agent_id = data.get("agent_id")
    
    notification = DetectionLog.query.get(notification_id)
    agent = User.query.filter_by(id=agent_id, role="agent").first()
    
    if not notification or not agent:
        return jsonify({"message": "Invalid notification or agent"}), 404

    # Build detailed message content
    details = {
        "event_type": notification.event_type,
        "timestamp": notification.timestamp.isoformat(),
        "stream_url": notification.room_url,
        "streamer": notification.details.get('streamer_name', 'Unknown'),
        "platform": notification.details.get('platform', 'Unknown')
    }

    # Add type-specific details
    if notification.event_type == 'object_detection':
        details.update({
            "detections": notification.details.get('detections', []),
            "annotated_image": base64.b64encode(notification.detection_image).decode('utf-8') 
                if notification.detection_image else None
        })
    elif notification.event_type == 'chat_detection':
        details.update({
            "keywords": notification.details.get('keywords', []),
            "messages": notification.details.get('detections', [])
        })
    elif notification.event_type == 'audio_detection':
        details.update({
            "keyword": notification.details.get('keyword'),
            "transcript": notification.details.get('transcript')
        })

    # Create system message
    sys_msg = ChatMessage(
        sender_id=session['user_id'],
        receiver_id=agent.id,
        message=f"🚨 Forwarded {notification.event_type.replace('_', ' ').title()} Alert",
        details=details,
        is_system=True,
        timestamp=datetime.utcnow()
    )
    
    db.session.add(sys_msg)
    db.session.commit()
    
    return jsonify({"message": "Notification forwarded", "message": sys_msg.serialize()}), 200