# routes/dashboard_routes.py
from flask import Blueprint, jsonify, session
from extensions import db
from models import Stream, Assignment
from utils import login_required
from sqlalchemy.orm import joinedload

dashboard_bp = Blueprint('dashboard', __name__)

# --------------------------------------------------------------------
# Dashboard Endpoints
# --------------------------------------------------------------------
@dashboard_bp.route("/api/dashboard", methods=["GET"])
@login_required
def get_dashboard():
    try:
        streams = Stream.query.options(joinedload(Stream.assignments).joinedload(Assignment.agent)).all()
        data = []
        for stream in streams:
            assignment = stream.assignments[0] if stream.assignments else None
            stream_data = {
                **stream.serialize(),
                "agent": assignment.agent.serialize() if assignment and assignment.agent else None,
                "confidence": 0.8
            }
            data.append(stream_data)
        return jsonify({
            "ongoing_streams": len(data),
            "streams": data
        }), 200
    except Exception as e:
        current_app.logger.error("Error in /api/dashboard: %s", e)
        return jsonify({"message": "Error fetching dashboard data", "error": str(e)}), 500

@dashboard_bp.route("/api/agent/dashboard", methods=["GET"])
@login_required
def get_agent_dashboard():
    agent_id = session["user_id"]
    assignments = Assignment.query.filter_by(agent_id=agent_id).all()
    return jsonify({
        "ongoing_streams": len(assignments),
        "assignments": [a.stream.serialize() for a in assignments if a.stream]
    })