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


@assignment_bp.route("/api/assignments", methods=["GET"])
@login_required(role="admin")
def get_assignments():
    stream_id = request.args.get("stream_id")
    agent_id = request.args.get("agent_id")
    
    query = Assignment.query
    
    if stream_id:
        query = query.filter_by(stream_id=stream_id)
    if agent_id:
        query = query.filter_by(agent_id=agent_id)
    
    assignments = query.all()
    return jsonify([a.serialize() for a in assignments])

@assignment_bp.route("/api/assignments/stream/<int:stream_id>", methods=["POST"])
@login_required(role="admin")
def manage_stream_assignments(stream_id):
    data = request.get_json()
    agent_ids = data.get("agent_ids", [])
    
    # Validate the stream exists
    stream = Stream.query.get(stream_id)
    if not stream:
        return jsonify({"message": "Stream not found"}), 404
    
    try:
        # Delete existing assignments
        Assignment.query.filter_by(stream_id=stream_id).delete()
        
        # Create new assignments
        created = []
        for agent_id in agent_ids:
            # Verify agent exists
            agent = User.query.filter_by(id=agent_id, role="agent").first()
            if agent:
                assignment = Assignment(agent_id=agent_id, stream_id=stream_id)
                db.session.add(assignment)
                created.append(agent_id)
        
        db.session.commit()
        return jsonify({
            "message": "Assignments updated successfully", 
            "assigned_agents": created
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Assignment update failed", "error": str(e)}), 500

@assignment_bp.route("/api/assignments/<int:assignment_id>", methods=["DELETE"])
@login_required(role="admin")
def delete_assignment(assignment_id):
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({"message": "Assignment not found"}), 404
    
    db.session.delete(assignment)
    db.session.commit()
    return jsonify({"message": "Assignment deleted successfully"}), 200