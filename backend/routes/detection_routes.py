# routes/detection_routes.py
from flask import Blueprint, request, jsonify, send_from_directory, Response, current_app, session
from extensions import db
from models import DetectionLog, Stream, Assignment, User, Log, ChatKeyword
from utils import login_required
import threading
import requests
import m3u8
import json
import numpy as np
import base64
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from utils.notifications import emit_notification, emit_stream_update


detection_bp = Blueprint('detection', __name__)
detection_threads = {}  # Global variable

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
    audio_flag = None
    visual_results = []
    
    # These functions need to be imported or defined elsewhere
    if visual_frame:
        from detection import detect_frame
        visual_results = detect_frame(np.array(visual_frame))
    
    from detection import detect_chat
    chat_results = detect_chat(text)
    
    return jsonify({
        "audio": audio_flag,
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

# Add or modify these routes in detection_routes.py

# Fix for detection_routes.py

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

    # If stream_id is provided, fetch the appropriate M3U8 URL
    if stream_id:
        stream = Stream.query.get(stream_id)
        if not stream:
            return jsonify({"error": "Stream not found"}), 404
        # Try to find an attribute ending with _m3u8_url
        stream_url = ''
        for attr in dir(stream):
            if attr.endswith('_m3u8_url'):
                stream_url = getattr(stream, attr, '')
                if stream_url:
                    break
        # Fallback to stream_url or room_url if no M3U8 URL is found
        if not stream_url:
            stream_url = getattr(stream, 'stream_url', getattr(stream, 'room_url', ''))
        if not stream_url:
            return jsonify({"error": "No valid URL found for stream"}), 400
        # Update stream status if available
        if hasattr(stream, 'status'):
            stream.status = 'online' if not stop else 'offline'
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

    # Check if we need to stop detection
    if stop:
        if stream_url in detection_threads:
            detection_thread, chat_thread, cancel_event = detection_threads[stream_url]
            cancel_event.set()
            detection_thread.join(timeout=2)
            chat_thread.join(timeout=2)
            del detection_threads[stream_url]
            return jsonify({"message": "Detection stopped successfully", "stream_url": stream_url, "stream_id": stream_id}), 200
        else:
            return jsonify({"message": "No detection running for this stream", "stream_url": stream_url, "stream_id": stream_id}), 404

    # Check if detection is already running
    if stream_url in detection_threads:
        return jsonify({"message": "Detection already running for this stream", "stream_url": stream_url, "stream_id": stream_id}), 200

    try:
        from detection import process_combined_detection, chat_detection_loop
        cancel_event = threading.Event()
        detection_thread = threading.Thread(
            target=process_combined_detection,
            args=(stream_url, cancel_event),
            daemon=True
        )
        detection_thread.start()
        chat_thread = threading.Thread(
            target=chat_detection_loop,
            args=(stream_url, cancel_event, 60),
            daemon=True
        )
        chat_thread.start()
        detection_threads[stream_url] = (detection_thread, chat_thread, cancel_event)
        return jsonify({"message": "Detection started successfully", "stream_url": stream_url, "stream_id": stream_id}), 200
    except Exception as e:
        return jsonify({"error": f"Error starting detection: {str(e)}"}), 500

@detection_bp.route("/api/detection-status/<int:stream_id>", methods=["GET"])
@login_required()
def detection_status(stream_id):
    stream = Stream.query.get_or_404(stream_id)
    stream_url = ''
    for attr in dir(stream):
        if attr.endswith('_m3u8_url'):
            stream_url = getattr(stream, attr, '')
            if stream_url:
                break
    if not stream_url:
        stream_url = getattr(stream, 'stream_url', getattr(stream, 'room_url', ''))
    is_active = stream_url in detection_threads
    stream_status = getattr(stream, 'status', 'unknown')
    return jsonify({
        "stream_id": stream_id,
        "stream_url": stream_url,
        "active": is_active,
        "status": stream_status
    })

