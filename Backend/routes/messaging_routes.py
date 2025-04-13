# routes/messaging_routes.py
from flask import Blueprint, request, jsonify, session
from extensions import db
from models import ChatMessage, User
from utils import login_required
from datetime import datetime

messaging_bp = Blueprint('messaging', __name__)

# --------------------------------------------------------------------
# Messaging Endpoints
# --------------------------------------------------------------------
@messaging_bp.route("/api/messages", methods=["POST"])
@login_required()
def send_message():
    data = request.get_json()
    receiver_id = data.get("receiver_id")
    message_text = data.get("message")

    if not receiver_id or not message_text:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        new_message = ChatMessage(
            sender_id=session["user_id"],
            receiver_id=receiver_id,
            message=message_text,
            timestamp=datetime.utcnow(),  # Fixed timestamp
            is_system=False
        )
        db.session.add(new_message)
        db.session.commit()
        return jsonify(new_message.serialize()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@messaging_bp.route("/api/messages/<int:receiver_id>", methods=["GET"])
@login_required()
def get_messages(receiver_id):
    user_id = session["user_id"]
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == receiver_id)) |
        ((ChatMessage.sender_id == receiver_id) & (ChatMessage.receiver_id == user_id))
    ).order_by(ChatMessage.timestamp.asc()).all()
    return jsonify([msg.serialize() for msg in messages])

@messaging_bp.route("/api/online-users", methods=["GET"])
@login_required()
def get_online_users():
    agents = User.query.filter(User.role.in_(["agent", "admin"])).all()
    return jsonify([{
        "id": agent.id,
        "username": agent.username,
        "online": agent.online,
        "last_active": agent.last_active.isoformat() if agent.last_active else None
    } for agent in agents])


# routes.py
@messaging_bp.route("/api/messages/mark-read", methods=["PUT"])
@login_required()
def mark_messages_read():
    data = request.get_json()
    message_ids = data.get("messageIds", [])
    
    ChatMessage.query.filter(ChatMessage.id.in_(message_ids)).update({"read": True})
    db.session.commit()
    return jsonify({"message": f"Marked {len(message_ids)} messages as read"})

@messaging_bp.route("/api/messages/<int:agent_id>", methods=["GET"])
@login_required()
def get_agent_messages(agent_id):
    # Check if user has valid session
    if "user_role" not in session or "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    # Authorization check
    if not (session['user_role'] == 'admin' or session['user_id'] == agent_id):
        return jsonify({"error": "Forbidden"}), 403

    try:
        messages = ChatMessage.query.filter(
            (ChatMessage.receiver_id == agent_id) |
            (ChatMessage.sender_id == agent_id)
        ).order_by(ChatMessage.timestamp.asc()).all()
        
        return jsonify([message.serialize() for message in messages])
    except Exception as e:
        return jsonify({"error": str(e)}), 500