# routes/detection_routes.py
from flask import Blueprint, request, jsonify, send_from_directory, session, current_app
from models import Stream
from utils import login_required
import requests
import m3u8
import numpy as np
from monitoring import start_monitoring, stop_monitoring, stream_processors

detection_bp = Blueprint('detection', __name__)

# Helper function to get stream URL
def get_stream_url(stream):
    """Get the appropriate stream URL (M3U8 or room URL) from a Stream object."""
    for attr in dir(stream):
        if attr.endswith('_m3u8_url'):
            stream_url = getattr(stream, attr, '')
            if stream_url:
                return stream_url
    # Fallback to stream_url or room_url
    return getattr(stream, 'stream_url', getattr(stream, 'room_url', ''))

# --------------------------------------------------------------------
# Detection and Notification Endpoints
# --------------------------------------------------------------------
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
        response = requests.get(m3u8_url, timeout=10)
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
@login_required(role=["admin", "agent"])
def trigger_detection():
    data = request.get_json()
    stream_id = data.get("stream_id")
    stop = data.get("stop", False)
    
    if not stream_id:
        return jsonify({"error": "Missing stream_id"}), 400

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    stream = Stream.query.get(stream_id)
    if not stream:
        return jsonify({"error": "Stream not found"}), 404

    stream_url = get_stream_url(stream)
    
    if stop:
        if stream.is_monitored or stream_url in stream_processors:
            try:
                stop_monitoring(stream)
                current_app.logger.info(f"Detection stopped for stream: {stream.id}")
                return jsonify({
                    "message": "Detection stopped successfully",
                    "stream_id": stream.id,
                    "active": False,
                    "status": stream.status or "unknown",
                    "isDetecting": False,
                    "isDetectionLoading": False,
                    "detectionError": None
                }), 200
            except Exception as e:
                current_app.logger.error(f"Error stopping detection for stream: {stream.id}: {str(e)}")
                return jsonify({
                    "error": f"Failed to stop detection: {str(e)}",
                    "stream_id": stream.id,
                    "active": stream.is_monitored,
                    "status": stream.status or "unknown",
                    "isDetecting": stream.is_monitored,
                    "isDetectionLoading": False,
                    "detectionError": str(e)
                }), 500
        else:
            current_app.logger.info(f"No active detection found for stream: {stream.id}")
            return jsonify({
                "message": "No active detection found for this stream",
                "stream_id": stream.id,
                "active": False,
                "status": stream.status or "unknown",
                "isDetecting": False,
                "isDetectionLoading": False,
                "detectionError": None
            }), 200

    # Check if detection is already running
    if stream.is_monitored or stream_url in stream_processors:
        current_app.logger.info(f"Detection already running for stream: {stream.id}")
        return jsonify({
            "message": "Detection already running for this stream",
            "stream_id": stream.id,
            "active": True,
            "status": stream.status or "unknown",
            "isDetecting": True,
            "isDetectionLoading": False,
            "detectionError": None
        }), 409  # Conflict status code

    # Start detection
    try:
        current_app.logger.info(f"Starting detection for stream: {stream.id}")
        if start_monitoring(stream):
            return jsonify({
                "message": "Detection started successfully",
                "stream_id": stream.id,
                "active": True,
                "status": stream.status or "unknown",
                "isDetecting": True,
                "isDetectionLoading": False,
                "detectionError": None
            }), 200
        else:
            current_app.logger.error(f"Failed to start monitoring for stream: {stream.id}")
            return jsonify({
                "error": "Failed to start monitoring",
                "stream_id": stream.id,
                "active": False,
                "status": stream.status or "unknown",
                "isDetecting": False,
                "isDetectionLoading": False,
                "detectionError": "Failed to start monitoring"
            }), 500
    except Exception as e:
        current_app.logger.error(f"Error starting detection for stream: {stream.id}: {str(e)}")
        return jsonify({
            "error": f"Error starting detection: {str(e)}",
            "stream_id": stream.id,
            "active": False,
            "status": stream.status or "unknown",
            "isDetecting": False,
            "isDetectionLoading": False,
            "detectionError": str(e)
        }), 500

@detection_bp.route("/api/detection-status/<int:stream_id>", methods=["GET"])
@login_required()
def detection_status(stream_id):
    stream = Stream.query.get_or_404(stream_id)
    stream_url = get_stream_url(stream)
    is_active = stream_url in stream_processors or stream.is_monitored
    stream_status = getattr(stream, 'status', 'unknown')
    return jsonify({
        "stream_id": stream_id,
        "stream_url": stream_url,
        "active": is_active,
        "status": stream_status,
        "isDetecting": is_active,
        "isDetectionLoading": False,  # Assume no loading state unless triggered
        "detectionError": None  # No error unless explicitly set
    })