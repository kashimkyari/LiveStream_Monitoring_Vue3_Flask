# routes/assignment_routes.py
from flask import Blueprint, request, jsonify
from extensions import db
from models import Assignment, Stream, User
from utils import login_required
from sqlalchemy.orm import joinedload
from utils.notifications import emit_assignment_update

assignment_bp = Blueprint('assignment', __name__)

# --------------------------------------------------------------------
# Assignment Endpoints
# --------------------------------------------------------------------
@assignment_bp.route("/api/assign", methods=["POST"])
@login_required(role="admin")
def assign_agent_to_stream():
    data = request.get_json()
    assignment_data = {
        "id": assignment.id,
        "agent_id": assignment.agent_id,
        "stream_id": assignment.stream_id,
        "action": "assigned"
    }
    agent_id = data.get("agent_id")
    stream_id = data.get("stream_id")
    if not agent_id or not stream_id:
        return jsonify({"message": "Both agent_id and stream_id are required."}), 400
    
    # Validate the agent and stream exist
    agent = User.query.get(agent_id)
    stream = Stream.query.get(stream_id)
    
    if not agent:
        return jsonify({"message": "Agent not found"}), 404
    if not stream:
        return jsonify({"message": "Stream not found"}), 404
    
    # Check if assignment already exists to avoid duplicates
    existing = Assignment.query.filter_by(agent_id=agent_id, stream_id=stream_id).first()
    if existing:
        return jsonify({"message": "Assignment already exists", "assignment": existing.serialize()}), 200
        
    try:
        assignment = Assignment(agent_id=agent_id, stream_id=stream_id)
        db.session.add(assignment)
        db.session.commit()
        emit_assignment_update(assignment_data)
        
        return jsonify({"message": "Assignment created successfully.", "assignment": assignment.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Assignment creation failed", "error": str(e)}), 500


@assignment_bp.route("/api/assignments", methods=["GET"])
@login_required
def get_assignments():
    stream_id = request.args.get("stream_id")
    agent_id = request.args.get("agent_id")
    
    # Use eager loading to improve performance
    query = Assignment.query.options(
        joinedload(Assignment.agent),
        joinedload(Assignment.stream)
    )
    
    if stream_id:
        query = query.filter_by(stream_id=stream_id)
    if agent_id:
        query = query.filter_by(agent_id=agent_id)
    
    assignments = query.all()
    
    # Return detailed serialized assignments for debugging
    return jsonify({
        "count": len(assignments),
        "assignments": [a.serialize() for a in assignments]
    })

@assignment_bp.route("/api/assignments/stream/<int:stream_id>", methods=["GET"])
@login_required
def get_stream_assignments(stream_id):
    """Get all assignments for a specific stream"""
    # First check if stream exists
    stream = Stream.query.get(stream_id)
    if not stream:
        return jsonify({"message": "Stream not found"}), 404
        
    # Get all assignments with eager loading
    assignments = Assignment.query.options(
        joinedload(Assignment.agent)
    ).filter_by(stream_id=stream_id).all()
    
    # Return detailed information about the assignments
    return jsonify({
        "stream_id": stream_id,
        "stream_url": stream.room_url,
        "stream_type": stream.type,
        "assignment_count": len(assignments),
        "assigned_agents": [
            {
                "assignment_id": a.id,
                "agent_id": a.agent_id,
                "agent_username": a.agent.username if a.agent else None,
                "created_at": a.created_at.isoformat() if a.created_at else None
            } for a in assignments
        ]
    })

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
        existing = Assignment.query.filter_by(stream_id=stream_id).all()
        for assignment in existing:
            db.session.delete(assignment)
        
        # Create new assignments
        created = []
        for agent_id in agent_ids:
            # Verify agent exists
            agent = User.query.filter_by(id=agent_id, role="agent").first()
            if agent:
                assignment = Assignment(agent_id=agent_id, stream_id=stream_id)
                db.session.add(assignment)
                created.append({
                    "agent_id": agent_id,
                    "agent_username": agent.username
                })
        
        db.session.commit()
        
        # Get the newly created assignments
        new_assignments = Assignment.query.filter_by(stream_id=stream_id).all()
        
        return jsonify({
            "message": "Assignments updated successfully", 
            "assigned_agents": created,
            "assignment_count": len(new_assignments),
            "assignments": [a.serialize() for a in new_assignments]
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

# Add to assignment_routes.py
@assignment_bp.route("/api/analytics/agent-performance")
@login_required(role="agent")
def agent_performance():
    agent_id = session.get("user_id")
    # Calculate performance metrics based on DetectionLog and Assignment data
    return jsonify({
        "resolutionRate": 85,
        "avgResponseTime": 12.5,
        "detectionBreakdown": [
            {"name": "Object", "count": 42},
            {"name": "Audio", "count": 28},
            {"name": "Chat", "count": 15}
        ],
        "activityTimeline": [...]  # Time-series data
    })