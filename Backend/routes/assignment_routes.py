# routes/assignment_routes.py
from flask import Blueprint, request, jsonify
from extensions import db
from models import Assignment
from utils import login_required

assignment_bp = Blueprint('assignment', __name__)

# --------------------------------------------------------------------
# Assignment Endpoints
# --------------------------------------------------------------------
@assignment_bp.route("/api/assign", methods=["POST"])
@login_required(role="admin")
def assign_agent_to_stream():
    data = request.get_json()
    agent_id = data.get("agent_id")
    stream_id = data.get("stream_id")
    if not agent_id or not stream_id:
        return jsonify({"message": "Both agent_id and stream_id are required."}), 400
    try:
        assignment = Assignment(agent_id=agent_id, stream_id=stream_id)
        db.session.add(assignment)
        db.session.commit()
        return jsonify({"message": "Assignment created successfully."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Assignment creation failed", "error": str(e)}), 500