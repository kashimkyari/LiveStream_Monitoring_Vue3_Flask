# routes/detection_routes.py
from flask import Blueprint, request, jsonify, send_from_directory, session, current_app
from models import Stream
from utils import login_required
from extensions import db
import requests
import m3u8
import numpy as np
import os

detection_bp = Blueprint('detection', __name__)

# Helper function to get stream URL
def get_stream_url(stream):
    """Get the appropriate stream URL (M3U8 or room URL) from a Stream object."""
    for attr in dir(stream):
        if attr.endswith('_m3u8_url'):
            stream_url = getattr(stream, attr, '')
            if stream_url:
                return stream_url
    return getattr(stream, 'stream_url', getattr(stream, 'room_url', ''))

# Get monitoring app URL from environment
MONITOR_API_URL = os.getenv('MONITOR_API_URL', 'https://monitor-backend.jetcamstudio.com:5001')

@detection_bp.route("/detection-images/<filename>")
def serve_detection_image(filename):
    return send_from_directory("detections", filename)

@detection_bp.route("/api/detect", methods=["POST"])
def unified_detect():
    data = request.get_json()
    text = data.get("text", "")
    visual_frame = data.get("visual_frame", None)
    visual_results = []
    
    if visual_frame:
        from monitoring import process_video_frame
        visual_results = process_video_frame(np.array(visual_frame), "unified_detect")
    
    from monitoring import process_chat_messages
    chat_results = process_chat_messages([{"message": text}], "unified_detect")
    
    return jsonify({
        "chat": chat_results,
        "visual": visual_results
    })

@detection_bp.route("/api/livestream", methods=["POST"])
def get_livestream():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Missing M3U8 URL"}), 400
    m3u8_url = data["url"]
    try:
        response = requests.get(m3u8_url, timeout=60)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch M3U8 file"}), 500
        playlist = m3u8.loads(response.text)
        if not playlist.playlists:
            return jsonify({"error": "No valid streams found"}), 400
        stream_url = playlist.playlists[0].uri
        return jsonify({"stream_url": stream_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@detection_bp.route("/api/trigger-detection", methods=["POST"])
def trigger_detection():
    current_app.logger.info("Received request to /api/trigger-detection")
    data = request.get_json()
    current_app.logger.info(f"Request data: {data}")
    stream_id = data.get("stream_id")
    stop = data.get("stop", False)
    current_app.logger.info(f"Stream ID: {stream_id}, Stop: {stop}")

    if not stream_id:
        return jsonify({"error": "Missing stream_id"}), 400

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Forward the request to the monitoring app
        response = requests.post(
            f"{MONITOR_API_URL}/api/monitor/trigger-detection",
            json={"stream_id": stream_id, "stop": stop},
            timeout=60
        )
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        current_app.logger.error(f"Error communicating with monitoring app: {str(e)}")
        return jsonify({
            "error": f"Failed to communicate with monitoring service: {str(e)}",
            "stream_id": stream_id,
            "active": False,
            "status": "unknown",
            "isDetecting": False,
            "isDetectionLoading": False,
            "detectionError": str(e)
        }), 500

@detection_bp.route("/api/detection-status/<int:stream_id>", methods=["GET"])
def detection_status(stream_id):
    try:
        # Query the monitoring app for real-time status
        response = requests.get(
            f"{MONITOR_API_URL}/api/monitor/detection-status/{stream_id}",
            timeout=60
        )
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        current_app.logger.error(f"Error communicating with monitoring app: {str(e)}")
        # Fallback to database query
        stream = Stream.query.get_or_404(stream_id)
        stream_url = get_stream_url(stream)
        is_active = stream.is_monitored and stream.status != 'offline'
        stream_status = getattr(stream, 'status', 'unknown')
        return jsonify({
            "stream_id": stream_id,
            "stream_url": stream_url,
            "active": is_active,
            "status": stream_status,
            "isDetecting": is_active,
            "isDetectionLoading": False,
            "detectionError": "Stream is offline" if stream.status == 'offline' else None
        }), 200

@detection_bp.route("/api/streams/<int:stream_id>/status", methods=["POST"])
def update_stream_status(stream_id):
    """Update the status of a stream."""
    data = request.get_json()
    if not data or "status" not in data:
        return jsonify({"error": "Missing status in request body"}), 400

    status = data.get("status")
    if status not in ["online", "offline", "monitoring"]:
        return jsonify({"error": "Invalid status value"}), 400

    stream = Stream.query.get(stream_id)
    if not stream:
        return jsonify({"error": "Stream not found"}), 404

    try:
        stream.status = status
        if status == 'offline':
            # Notify monitoring app to stop detection
            requests.post(
                f"{MONITOR_API_URL}/api/monitor/trigger-detection",
                json={"stream_id": stream_id, "stop": True},
                timeout=60
            )
        db.session.commit()
        current_app.logger.info(f"Stream {stream_id} status updated to {status}")
        return jsonify({
            "message": "Stream status updated successfully",
            "stream_id": stream_id,
            "status": stream.status
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating stream {stream_id} status: {str(e)}")
        return jsonify({"error": f"Failed to update stream status: {str(e)}"}), 500