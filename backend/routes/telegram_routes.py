from flask import Blueprint, request, jsonify
from extensions import db
from models import TelegramRecipient
from utils import login_required

telegram_bp = Blueprint('telegram', __name__)

@telegram_bp.route("/api/telegram_recipients", methods=["GET"])
@login_required
def get_telegram_recipients():
    recipients = TelegramRecipient.query.all()
    return jsonify([r.serialize() for r in recipients])

@telegram_bp.route("/api/telegram_recipients", methods=["POST"])
@login_required()
def create_telegram_recipient():
    data = request.get_json()
    username = data.get("telegram_username")
    chat_id = data.get("chat_id")
    if not username or not chat_id:
        return jsonify({"message": "Telegram username and chat_id required"}), 400
    if TelegramRecipient.query.filter_by(telegram_username=username).first():
        return jsonify({"message": "Recipient exists"}), 400
    recipient = TelegramRecipient(telegram_username=username, chat_id=chat_id)
    db.session.add(recipient)
    db.session.commit()
    return jsonify({"message": "Recipient added", "recipient": recipient.serialize()}), 201

@telegram_bp.route("/api/telegram_recipients/<int:recipient_id>", methods=["DELETE"])
@login_required(role="admin")
def delete_telegram_recipient(recipient_id):
    recipient = TelegramRecipient.query.get(recipient_id)
    if not recipient:
        return jsonify({"message": "Recipient not found"}), 404
    db.session.delete(recipient)
    db.session.commit()
    return jsonify({"message": "Recipient deleted"})
