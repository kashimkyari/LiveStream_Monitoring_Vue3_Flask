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
    stream_url = data.get("stream_url")
    stream_id = data.get("stream_id")
    stop = data.get("stop", False)
    
    if not stream_url and not stream_id:
        return jsonify({"error": "Missing stream_url or stream_id"}), 400

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    # If stream_id is provided, fetch the appropriate stream URL
    if stream_id:
        stream = Stream.query.get(stream_id)
        if not stream:
            return jsonify({"error": "Stream not found"}), 404
        stream_url = get_stream_url(stream)
        if not stream_url:
            return jsonify({"error": "No valid URL found for stream"}), 400
    else:
        # Validate stream_url if provided directly
        stream = Stream.query.filter_by(room_url=stream_url).first()
        if not stream:
            stream = Stream.query.filter(
                (Stream.chaturbate_m3u8_url == stream_url) |
                (Stream.stripchat_m3u8_url == stream_url)
            ).first()
        if not stream:
            return jsonify({"error": "Stream not found for provided URL"}), 404

    # Stop detection if requested
    if stop:
        if stream_url in stream_processors:
            stop_monitoring(stream_url)
            current_app.logger.info(f"Detection stopped for stream_url: {stream_url}")
            return jsonify({
                "message": "Detection stopped successfully",
                "stream_url": stream_url,
                "stream_id": stream.id
            }), 200
        else:
            current_app.logger.info(f"No active detection found for stream_url: {stream_url}")
            return jsonify({
                "message": "No active detection found for this stream",
                "stream_url": stream_url,
                "stream_id": stream.id
            }), 200

    # Check if detection is already running
    if stream_url in stream_processors or stream.is_monitored:
        current_app.logger.info(f"Detection already running for stream_url: {stream_url}")
        return jsonify({
            "message": "Detection already running for this stream",
            "stream_url": stream_url,
            "stream_id": stream.id
        }), 409  # Conflict status code

    # Start detection
    try:
        current_app.logger.info(f"Starting detection for stream_url: {stream_url}")
        if start_monitoring(stream_url):
            return jsonify({
                "message": "Detection started successfully",
                "stream_url": stream_url,
                "stream_id": stream.id
            }), 200
        else:
            current_app.logger.error(f"Failed to start monitoring for stream_url: {stream_url}")
            return jsonify({"error": "Failed to start monitoring"}), 500
    except Exception as e:
        current_app.logger.error(f"Error starting detection for stream_url: {stream_url}: {str(e)}")
        return jsonify({"error": f"Error starting detection: {str(e)}"}), 500

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
        "status": stream_status
    })