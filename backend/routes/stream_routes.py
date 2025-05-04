from datetime import datetime, timedelta 
import re
from flask import current_app
from flask import Blueprint, request, jsonify
from extensions import db
from models import Stream, ChaturbateStream, StripchatStream, DetectionLog, Assignment, User
from utils import login_required
from scraping import scrape_chaturbate_data, scrape_stripchat_data, stream_creation_jobs, run_stream_creation_job
import uuid
import threading
from sqlalchemy.orm import joinedload
import logging
# Import the notification emitter
from utils.notifications import emit_notification, emit_stream_update

detection_threads = {}  # Moved here if needed

stream_bp = Blueprint('stream', __name__)

# --------------------------------------------------------------------
# Stream Management Endpoints
# --------------------------------------------------------------------
@stream_bp.route("/api/streams", methods=["GET"])
def get_streams():
    platform = request.args.get("platform", "").strip().lower()
    streamer = request.args.get("streamer", "").strip().lower()
    if platform == "chaturbate":
        streams = ChaturbateStream.query.options(
            joinedload(ChaturbateStream.assignments).joinedload(Assignment.agent)
        ).filter(ChaturbateStream.streamer_username.ilike(f"%{streamer}%")).all()
    elif platform == "stripchat":
        streams = StripchatStream.query.options(
            joinedload(StripchatStream.assignments).joinedload(Assignment.agent)
        ).filter(StripchatStream.streamer_username.ilike(f"%{streamer}%")).all()
    else:
        # Updated with eager loading
        streams = Stream.query.options(
            joinedload(Stream.assignments).joinedload(Assignment.agent)
        ).all()
    return jsonify([stream.serialize() for stream in streams])

@stream_bp.route("/api/streams", methods=["POST"])
@login_required(role="admin")
def create_stream():
    data = request.get_json()
    platform = data.get("platform", "Chaturbate").strip()
    room_url = data.get("room_url", "").strip().lower()
    if not room_url:
        return jsonify({"message": "Room URL required"}), 400
    if platform.lower() == "chaturbate" and "chaturbate.com/" not in room_url:
        return jsonify({"message": "Invalid Chaturbate URL"}), 400
    if platform.lower() == "stripchat" and "stripchat.com/" not in room_url:
        return jsonify({"message": "Invalid Stripchat URL"}), 400
    if Stream.query.filter_by(room_url=room_url).first():
        return jsonify({"message": "Stream exists"}), 400

    streamer_username = room_url.rstrip("/").split("/")[-1]
    if platform.lower() == "chaturbate":
        scraped_data = scrape_chaturbate_data(room_url)
        if not scraped_data or 'chaturbate_m3u8_url' not in scraped_data:
            return jsonify({"message": "Failed to scrape Chaturbate details"}), 500
        stream = ChaturbateStream(
            room_url=room_url,
            streamer_username=streamer_username,
            type="chaturbate",
            chaturbate_m3u8_url=scraped_data["chaturbate_m3u8_url"],
        )
    elif platform.lower() == "stripchat":
        scraped_data = scrape_stripchat_data(room_url)
        if not scraped_data or 'stripchat_m3u8_url' not in scraped_data:
            return jsonify({"message": "Failed to scrape Stripchat details"}), 500
        stream = StripchatStream(
            room_url=room_url,
            streamer_username=streamer_username,
            type="stripchat",
            stripchat_m3u8_url=scraped_data["stripchat_m3u8_url"],
        )
    else:
        return jsonify({"message": "Invalid platform"}), 400

    db.session.add(stream)
    db.session.commit()

    # Auto-assign to agent with least assignments and online if possible
    agents = User.query.filter_by(role="agent").all()
    if agents:
        # Calculate workload for each agent
        agent_workload = {}
        for agent in agents:
            assignment_count = Assignment.query.filter_by(agent_id=agent.id).count()
            agent_workload[agent.id] = {
                "count": assignment_count,
                "online": agent.online
            }
        # Find agent with least assignments, prioritizing online agents
        selected_agent_id = None
        min_assignments = float('inf')
        for agent_id, workload in agent_workload.items():
            if workload["online"] and workload["count"] < min_assignments:
                selected_agent_id = agent_id
                min_assignments = workload["count"]
        if not selected_agent_id:  # If no online agents, pick the one with least assignments
            for agent_id, workload in agent_workload.items():
                if workload["count"] < min_assignments:
                    selected_agent_id = agent_id
                    min_assignments = workload["count"]
        if selected_agent_id:
            assignment = Assignment(agent_id=selected_agent_id, stream_id=stream.id)
            db.session.add(assignment)
            db.session.commit()
            # Optionally notify the agent here

    # Inside the create_stream function within stream_routes.py
    # After creating the DetectionLog entry:

    # Prepare notification data for Socket.IO
    detection_log = DetectionLog(
        room_url=room_url,
        event_type="stream_created",
        details={
            "message": "Stream created",
            "streamer_username": streamer_username,
            "platform": platform.lower(),
            "stream_url": room_url
        },
        read=False  # Default to unread.
    )
    db.session.add(detection_log)
    db.session.commit()

    detection_log_data = {
        "id": detection_log.id,
        "event_type": "stream_created",
        "timestamp": detection_log.timestamp.isoformat(),
        "details": detection_log.details,
        "read": False,
        "room_url": room_url,
        "streamer": streamer_username,
        "platform": platform.lower()
    }

    # Emit notification about new stream
    emit_notification(detection_log_data)

    # Also emit stream update event
    stream_data = {
        "id": stream.id,
        "type": stream.type,
        "room_url": stream.room_url,
        "streamer_username": stream.streamer_username,
        "action": "created"
    }
    emit_stream_update(stream_data)

    # Send Telegram alert to all recipients about the new stream.
    try:
        from models import TelegramRecipient
        from notifications import send_text_message, executor
        
        recipients = TelegramRecipient.query.all()
        alert_message = (
            f"🚨 New Stream Created\n"
            f"Platform: {platform}\n"
            f"Streamer: {streamer_username}\n"
            f"Room URL: {room_url}"
        )
        for recipient in recipients:
            executor.submit(send_text_message, alert_message, recipient.chat_id, None)
    except Exception as e:
        logging.error("Error sending Telegram alert for stream creation: %s", e)

    return jsonify({"message": "Stream created", "stream": stream.serialize()}), 201

@stream_bp.route("/api/streams/<int:stream_id>", methods=["PUT"])
@login_required(role="admin")
def update_stream(stream_id):
    stream = Stream.query.get(stream_id)
    if not stream:
        return jsonify({"message": "Stream not found"}), 404
    
    data = request.get_json()
    agent_ids_only = len(data.keys()) == 1 and "agent_ids" in data
    
    # Update only the fields that are provided
    if "room_url" in data and data["room_url"].strip():
        # Check if new URL already exists for another stream
        existing = Stream.query.filter(Stream.room_url == data["room_url"].strip(), Stream.id != stream_id).first()
        if existing:
            return jsonify({"message": "Room URL already exists for another stream"}), 400
        stream.room_url = data["room_url"].strip()
    
    # Check if we need to refresh the stream data
    # Only refresh if explicitly requested AND we're not just updating agent assignments
    if "refresh" in data and data["refresh"] and not agent_ids_only:
        if stream.type == "chaturbate":
            child_stream = ChaturbateStream.query.get(stream_id)
            scraped_data = scrape_chaturbate_data(stream.room_url)
            if scraped_data and 'chaturbate_m3u8_url' in scraped_data:
                child_stream.chaturbate_m3u8_url = scraped_data["chaturbate_m3u8_url"]
        elif stream.type == "stripchat":
            child_stream = StripchatStream.query.get(stream_id)
            scraped_data = scrape_stripchat_data(stream.room_url)
            if scraped_data and 'stripchat_m3u8_url' in scraped_data:
                child_stream.stripchat_m3u8_url = scraped_data["stripchat_m3u8_url"]
    
    # Handle agent assignments
    if "agent_ids" in data:
        # Clear existing assignments if we're setting new ones
        existing_assignments = Assignment.query.filter_by(stream_id=stream_id).all()
        for assignment in existing_assignments:
            db.session.delete(assignment)
        
        # Create new assignments for each agent
        for agent_id in data["agent_ids"]:
            # Verify agent exists
            agent = User.query.filter_by(id=agent_id, role="agent").first()
            if agent:
                assignment = Assignment(agent_id=agent_id, stream_id=stream_id)
                db.session.add(assignment)
    
    db.session.commit()
    return jsonify({"message": "Stream updated", "stream": stream.serialize()}), 200

# Modify the existing delete function to handle assignments
@stream_bp.route("/api/streams/<int:stream_id>", methods=["DELETE"])
@login_required(role="admin")
def delete_stream(stream_id):
    stream = Stream.query.get(stream_id)
    if not stream:
        return jsonify({"message": "Stream not found"}), 404

    

    db.session.delete(stream)
    db.session.commit()
    return jsonify({"message": "Stream deleted"}), 200



# --------------------------------------------------------------------
# Updated Stream Refresh Route for Chaturbate
# --------------------------------------------------------------------
@stream_bp.route("/api/streams/refresh/chaturbate", methods=["POST"])
@login_required(role="admin")
def refresh_chaturbate_route():
    data = request.get_json()
    room_slug = data.get("room_slug", "").strip()
    if not room_slug:
        return jsonify({"message": "Room slug is required"}), 400

    new_url = refresh_chaturbate_stream(room_slug)
    if new_url:
        return jsonify({
            "message": "Stream refreshed successfully",
            "m3u8_url": new_url
        }), 200
    else:
        return jsonify({"message": "Failed to refresh stream"}), 500

# --------------------------------------------------------------------
# Interactive Stream Creation Endpoints
# --------------------------------------------------------------------
@stream_bp.route("/api/streams/interactive", methods=["POST"])
@login_required(role="admin")
def interactive_create_stream():
    """Enhanced stream creation endpoint with full validation"""
    try:
        # Validate request format
        if not request.is_json:
            return jsonify({
                "message": "Request must be JSON",
                "error": "invalid_content_type"
            }), 400

        data = request.get_json()
        required_fields = ["room_url", "platform"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return jsonify({
                "message": f"Missing required fields: {', '.join(missing)}",
                "error": "missing_fields",
                "missing": missing
            }), 400

        # Extract and sanitize inputs
        room_url = data.get("room_url", "").strip().lower()
        platform = data.get("platform", "").strip().lower()
        raw_agent_id = data.get("agent_id")

        # Validate URL structure
        if not room_url:
            return jsonify({
                "message": "Room URL cannot be empty",
                "error": "invalid_url"
            }), 400

        # Platform validation matrix
        platform_validations = {
            "chaturbate": {
                "domain": "chaturbate.com",
                "model": ChaturbateStream,
                "url_pattern": r"https?://(www\.)?chaturbate\.com/[a-zA-Z0-9_]+/?$"
            },
            "stripchat": {
                "domain": "stripchat.com",
                "model": StripchatStream,
                "url_pattern": r"https?://(www\.)?stripchat\.com/[a-zA-Z0-9_]+/?$"
            }
        }

        if platform not in platform_validations:
            return jsonify({
                "message": f"Invalid platform. Valid options: {', '.join(platform_validations.keys())}",
                "error": "invalid_platform"
            }), 400

        # URL format validation
        platform_config = platform_validations[platform]
        if not re.match(platform_config["url_pattern"], room_url):
            return jsonify({
                "message": f"Invalid {platform} URL format",
                "error": "invalid_url_format",
                "example": f"https://{platform_config['domain']}/username"
            }), 400

        # Agent ID validation
        agent_id = None
        if raw_agent_id not in [None, ""]:
            try:
                agent_id = int(raw_agent_id)
                agent = User.query.filter_by(id=agent_id, role="agent").first()
                if not agent:
                    return jsonify({
                        "message": "Specified agent does not exist",
                        "error": "invalid_agent_id"
                    }), 400
            except ValueError:
                return jsonify({
                    "message": "Agent ID must be a valid integer",
                    "error": "invalid_agent_format"
                }), 400

        # Check for existing stream
        existing_stream = Stream.query.filter_by(room_url=room_url).first()
        if existing_stream:
            return jsonify({
                "message": "Stream already exists",
                "error": "duplicate_stream",
                "existing_id": existing_stream.id
            }), 409  # Conflict status code

        # Create stream job
        job_id = str(uuid.uuid4())
        stream_creation_jobs[job_id] = {
            "progress": 0,
            "message": "Initializing",
            "created_at": datetime.now().isoformat(),
            "room_url": room_url,
            "platform": platform,
            "agent_id": agent_id
        }

        # Start processing thread
        threading.Thread(
            target=run_stream_creation_job,
            args=(current_app._get_current_object(), job_id, room_url, platform, agent_id),
            daemon=True
        ).start()

        return jsonify({
            "message": "Stream creation started",
            "job_id": job_id,
            "monitor_url": f"/api/streams/interactive/sse?job_id={job_id}"
        }), 202

    except Exception as e:
        logging.error("Unexpected error in stream creation: %s", str(e))
        return jsonify({
            "message": "Internal server error",
            "error": "server_error",
            "details": str(e)
        }), 500


@stream_bp.route("/api/streams/interactive/sse")
@login_required(role="admin")
def stream_creation_sse():
    job_id = request.args.get("job_id")
    if not job_id:
        return jsonify({"message": "Job id required"}), 400
    
    # Import required modules
    import json
    import time
    from flask import Response
        
    def event_stream():
        from scraping import stream_creation_jobs
        try:
            while True:
                job_status = stream_creation_jobs.get(job_id)
                if not job_status:
                    yield "event: error\ndata: {'message': 'Job not found'}\n\n"
                    break
                
                # Send progress updates
                data = json.dumps({
                    "progress": job_status["progress"],
                    "message": job_status["message"],
                    "error": job_status.get("error"),
                    "estimated_time": job_status.get("estimated_time")
                })
                yield f"data: {data}\n\n"
                
                # Exit conditions
                if job_status["progress"] >= 100 or job_status.get("error"):
                    if "stream_data" in job_status:
                        yield f"event: completed\ndata: {json.dumps(job_status['stream_data'])}\n\n"
                    break
                    
                time.sleep(1)
        except GeneratorExit:
            # Cleanup when client disconnects
            if job_id in stream_creation_jobs:
                del stream_creation_jobs[job_id]

    return Response(event_stream(), mimetype="text/event-stream")

@stream_bp.route("/api/streams/interactive/status", methods=["GET"])
@login_required(role="admin")
def stream_creation_status():
    job_id = request.args.get("job_id")
    if not job_id:
        return jsonify({"message": "Job ID required"}), 400
    
    job_status = stream_creation_jobs.get(job_id)
    if not job_status:
        return jsonify({"message": "Job not found", "error": "Job not found"}), 404
    
    # Return current status
    return jsonify({
        "progress": job_status["progress"],
        "message": job_status["message"],
        "error": job_status.get("error"),
        "estimated_time": job_status.get("estimated_time"),
        "stream_data": job_status.get("stream_data")
    })

    
@stream_bp.route("/api/streams/interactive/cleanup", methods=["POST"])
@login_required(role="admin")
def cleanup_jobs():
    from scraping import stream_creation_jobs
    expired_jobs = [
        job_id for job_id, job in stream_creation_jobs.items()
        if job["progress"] >= 100 or 
        (datetime.now() - job.get("created_at", datetime.now())) > timedelta(hours=1)
    ]
    
    for job_id in expired_jobs:
        del stream_creation_jobs[job_id]
        
    return jsonify({
        "message": f"Cleaned up {len(expired_jobs)} old jobs",
        "remaining_jobs": len(stream_creation_jobs)
    })

# Add this function in stream_routes.py
@stream_bp.route("/api/streams/refresh/stripchat", methods=["POST"])
def refresh_stripchat_stream(room_url):
    from scraping import scrape_stripchat_data  # Ensure import if not already present
    
    # Scrape fresh data
    scraped_data = scrape_stripchat_data(room_url)
    if not scraped_data or 'stripchat_m3u8_url' not in scraped_data:
        return None
    
    # Update the database entry
    stream = StripchatStream.query.filter_by(room_url=room_url).first()
    if stream:
        stream.stripchat_m3u8_url = scraped_data['stripchat_m3u8_url']
        db.session.commit()
    
    return scraped_data['stripchat_m3u8_url']



@login_required(role="admin")
def refresh_stripchat_route():
    data = request.get_json()
    room_url = data.get("room_url", "").strip()
    if not room_url:
        return jsonify({"message": "Room URL is required"}), 400

    new_url = refresh_stripchat_stream(room_url)
    if new_url:
        return jsonify({
            "message": "Stream refreshed successfully",
            "m3u8_url": new_url
        }), 200
    else:
        return jsonify({"message": "Failed to refresh stream"}), 500

# Endpoint to update stream status
@stream_bp.route('/api/streams/<int:stream_id>/status', methods=['POST'])
@login_required(role='admin')
def update_stream_status(stream_id):
    stream = Stream.query.get(stream_id)
    if not stream:
        return jsonify({'message': 'Stream not found'}), 404
    
    data = request.get_json()
    status = data.get('status')
    if status not in ['online', 'offline']:
        return jsonify({'message': 'Invalid status. Use online or offline'}), 400
    
    stream.status = status
    db.session.commit()
    
    # Emit update to connected clients
    stream_data = {
        'id': stream.id,
        'type': stream.type,
        'room_url': stream.room_url,
        'streamer_username': stream.streamer_username,
        'status': stream.status,
        'action': 'status_update'
    }
    emit_stream_update(stream_data)
    
    return jsonify({'message': f'Stream status updated to {status}', 'stream': stream.serialize()}), 200