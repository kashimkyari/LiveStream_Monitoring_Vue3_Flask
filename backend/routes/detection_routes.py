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
from monitoring import process_combined_detection, start_monitoring, stop_monitoring

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

    # Stop detection if requested
    if stop:
        return stop_monitoring(stream_url)
    
    # Start detection
    try:
        if start_monitoring(stream_url):
            return jsonify({
                "message": "Detection started successfully", 
                "stream_url": stream_url, 
                "stream_id": stream_id
            }), 200
        else:
            return jsonify({"error": "Failed to start monitoring"}), 500
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

