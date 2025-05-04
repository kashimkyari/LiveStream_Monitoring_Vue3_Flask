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
from utils.notifications import emit_notification


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
    stop = data.get("stop", False)
    
    if not stream_url:
        return jsonify({"error": "Missing stream_url"}), 400

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    # Check if we need to stop detection
    if stop:
        if stream_url in detection_threads:
            # Fix: The stored object is a tuple containing threads and the cancel_event
            # We need to unpack it correctly
            detection_thread, chat_thread, cancel_event = detection_threads[stream_url]
            
            # Set the cancel event to stop the threads
            cancel_event.set()
            
            # Wait for threads to finish (with timeout)
            detection_thread.join(timeout=2)
            chat_thread.join(timeout=2)
            
            # Remove from detection_threads
            del detection_threads[stream_url]
            return jsonify({"message": "Detection stopped successfully"}), 200
        else:
            return jsonify({"message": "No detection running for this stream"}), 404

    # Check if detection is already running
    if stream_url in detection_threads:
        return jsonify({"message": "Detection already running for this stream"}), 200

    # Removed strict HTTP status code check to allow detection start even if direct access fails
    try:
        # Import detection modules
        from detection import process_combined_detection, chat_detection_loop
        
        # Create cancel event
        cancel_event = threading.Event()
        
        # Start detection threads
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
        
        # Fix: Store threads and cancel event in the correct order
        detection_threads[stream_url] = (detection_thread, chat_thread, cancel_event)
        
        return jsonify({"message": "Detection started successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Error starting detection: {str(e)}"}), 500

# Add a route to check detection status
@detection_bp.route("/api/detection-status/<int:stream_id>", methods=["GET"])
@login_required()
def detection_status(stream_id):
    # Find the stream by ID
    stream = Stream.query.get_or_404(stream_id)
    # Check if detection is active for this stream
    is_active = stream.stream_url in detection_threads
    return jsonify({
        "stream_id": stream_id,
        "stream_url": stream.stream_url,
        "active": is_active
    })

