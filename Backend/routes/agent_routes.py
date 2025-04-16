# routes/agent_routes.py
from flask import Blueprint, request, jsonify, session
from extensions import db
from models import User, Assignment
from utils import login_required

agent_bp = Blueprint('agent', __name__)

# --------------------------------------------------------------------
# Agent Management Endpoints
# --------------------------------------------------------------------
@agent_bp.route("/api/agents", methods=["GET"])
@login_required(role="admin")
def get_agents():
    agents = User.query.filter_by(role="agent").all()
    return jsonify([agent.serialize() for agent in agents])

@agent_bp.route("/api/agents", methods=["POST"])
@login_required(role="admin")
def create_agent():
    data = request.get_json()
    required_fields = ["username", "password"]
    if any(field not in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"message": "Username already exists"}), 400
    
    agent = User(
        username=data["username"],
        password=data["password"],
        role="agent",
    )
    db.session.add(agent)
    db.session.commit()
    return jsonify({"message": "Agent created", "agent": agent.serialize()}), 201

@agent_bp.route("/api/agents/<int:agent_id>", methods=["PUT"])
@login_required(role="admin")
def update_agent(agent_id):
    agent = User.query.filter_by(id=agent_id, role="agent").first()
    if not agent:
        return jsonify({"message": "Agent not found"}), 404
    data = request.get_json()
    
    if "username" in data and (new_uname := data["username"].strip()):
        if User.query.filter(User.username == new_uname, User.id != agent_id).first():
            return jsonify({"message": "Username already taken"}), 400
        agent.username = new_uname
    
    if "password" in data and (new_pwd := data["password"].strip()):
        agent.password = new_pwd
    
    if "online" in data:
        agent.online = bool(data["online"])
    
    db.session.commit()
    return jsonify({"message": "Agent updated", "agent": agent.serialize()})

@agent_bp.route("/api/agents/<int:agent_id>", methods=["DELETE"])
@login_required(role="admin")
def delete_agent(agent_id):
    agent = User.query.filter_by(id=agent_id, role="agent").first()
    if not agent:
        return jsonify({"message": "Agent not found"}), 404
    db.session.delete(agent)
    db.session.commit()
    return jsonify({"message": "Agent deleted"})

# Add a new endpoint to get streams assigned to an agent
@agent_bp.route("/api/agents/<int:agent_id>/assignments", methods=["GET"])
@login_required(role="admin")
def get_agent_assignments(agent_id):
    agent = User.query.filter_by(id=agent_id, role="agent").first()
    if not agent:
        return jsonify({"message": "Agent not found"}), 404
    
    assignments = agent.assignments
    return jsonify([assignment.serialize() for assignment in assignments])