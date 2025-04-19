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

@detection_bp.route("/api/trigger-detection", methods=["POST"])
@login_required()  # Ensure that a user is logged in.
def trigger_detection():
    data = request.get_json()
    stream_url = data.get("stream_url")
    if not stream_url:
        return jsonify({"error": "Missing stream_url"}), 400

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response = requests.get(stream_url, timeout=10)
        if response.status_code != 200:
            return jsonify({"error": "Stream appears offline"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    try:
        from detection import process_combined_detection, chat_detection_loop
    except ImportError as e:
        return jsonify({"error": f"Detection module not available: {str(e)}"}), 500

    if stream_url in detection_threads:
        return jsonify({"message": "Detection already running for this stream"}), 200

    cancel_event = threading.Event()
    unified_thread = threading.Thread(
        target=process_combined_detection,
        args=(stream_url, cancel_event),
        daemon=True
    )
    unified_thread.start()
    chat_thread = threading.Thread(
        target=chat_detection_loop,
        args=(stream_url, cancel_event, 60),
        daemon=True
    )
    chat_thread.start()
    detection_threads[stream_url] = (unified_thread, chat_thread, cancel_event)

    return jsonify({"message": "Detection started"}), 200

@detection_bp.route("/api/detect-advanced", methods=["POST"])
def advanced_detect():
    try:
        data = request.get_json(silent=True)
        
        # Handle form data with chat image
        if 'chat_image' in request.files:
            room_url = request.form.get("stream_url")
            if "chaturbate.com" in room_url:
                room_slug = room_url.rstrip("/").split("/")[-1]
                # This function needs to be imported or defined elsewhere
                from scraping import fetch_chaturbate_chat_history
                chat_messages = fetch_chaturbate_chat_history(room_slug)
                flagged_keywords = [kw.keyword for kw in ChatKeyword.query.all()]
                
                detected = []
                for msg in chat_messages:
                    msg_data = msg.get("RoomMessageTopic#RoomMessageTopic:0YJW2WC", {})
                    message = msg_data.get("message", "")
                    sender = msg_data.get("from_user", {}).get("username", "unknown")
                    
                    detected_keywords = [
                        kw for kw in flagged_keywords 
                        if kw.lower() in message.lower()
                    ]
                    
                    if detected_keywords:
                        detected.append({
                            "message": message,
                            "sender": sender,
                            "keywords": detected_keywords
                        })

                if detected:
                    stream = Stream.query.filter_by(room_url=room_url).first()
                    log_entry = DetectionLog(
                        room_url=room_url,
                        event_type="chat_detection",
                        details={
                            "detections": detected,
                            "platform": "Chaturbate",
                            "streamer_name": stream.streamer_username if stream else "Unknown"
                        }

                    )
                    db.session.add(log_entry)
                    db.session.commit()
                    notification_data = {
                        "id": log_entry.id,
                        "event_type": log_entry.event_type,
                        "timestamp": log_entry.timestamp.isoformat(),
                        "details": log_entry.details,
                        "read": log_entry.read,
                        "room_url": log_entry.room_url
                    }

                    # Emit notification
                    emit_notification(notification_data)
                    return jsonify({"detections": detected}), 200
        
        # Handle JSON data
        if data is None:
            return jsonify({"message": "No valid JSON or files provided"}), 400
        
        # Process by event type
        if "type" in data:
            event_type = data.get('type')
            stream_url = data.get('stream_url')
            timestamp_str = data.get('timestamp')
            timestamp_obj = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.utcnow()
            log_entry = Log(
                room_url=stream_url,
                timestamp=timestamp_obj,
                read=False
            )
            if event_type == 'visual':
                log_entry.event_type = 'object_detection'
                log_entry.details = {
                    'detections': data.get('detections'),
                    'annotated_image': data.get('annotated_image'),
                    'confidence': data.get('confidence'),
                    'streamer_name': data.get('streamer_name'),
                    'platform': data.get('platform')
                }
            elif event_type == 'audio':
                log_entry.event_type = 'audio_detection'
                log_entry.details = {
                    'keyword': data.get('keyword'),
                    'confidence': data.get('confidence'),
                    'streamer_name': data.get('streamer_name'),
                    'platform': data.get('platform')
                }
            else:
                return jsonify({"error": "Invalid event type"}), 400
            
            db.session.add(log_entry)
            db.session.commit()
            
            # Function needs to be imported or defined elsewhere
            from notifications import send_notifications
            send_notifications(log_entry)
            
            return jsonify({"message": "JSON-based detection logged"}), 201
        
        # Process keyword detection
        if "keyword" in data:
            keyword = data.get("keyword")
            timestamp = data.get("timestamp")
            stream_url = data.get("stream_url")
            if not keyword or not timestamp or not stream_url:
                return jsonify({"message": "Missing required fields"}), 400
            log_entry = Log(
                room_url=stream_url,
                event_type="audio_detection",
                details={
                    "keyword": keyword,
                    "timestamp": timestamp,
                }
            )
            db.session.add(log_entry)
            db.session.commit()
            
            # Function needs to be imported or defined elsewhere
            from notifications import send_notifications
            send_notifications(log_entry, {"keyword": keyword})
            
            return jsonify({"message": "Keyword detection logged successfully"}), 201
        
        # Process detection with detections
        if "detections" in data:
            stream_url = data.get("stream_url")
            detections = data.get("detections", [])
            annotated_image = data.get("annotated_image")
            captured_image = data.get("captured_image")
            timestamp = data.get("timestamp")
            
            if not stream_url or not detections:
                return jsonify({"message": "Missing required fields"}), 400
            
            # Updated stream query with eager loading
            stream = Stream.query.options(
                joinedload(Stream.assignments).joinedload(Assignment.agent)
            ).filter_by(room_url=stream_url).first()
            
            platform = stream.type if stream else "unknown"
            streamer_name = stream.streamer_username if stream else "unknown"
            
            # Get first valid assigned agent
            assigned_agent = "Unassigned"
            if stream and stream.assignments:
                for assignment in stream.assignments:
                    if assignment.agent:
                        assigned_agent = assignment.agent.username
                        break  # Use first valid assignment
            
            log_entry = Log(
                room_url=stream_url,
                event_type="object_detection",
                details={
                    "detections": detections,
                    "annotated_image": annotated_image,
                    "captured_image": captured_image,
                    "timestamp": timestamp,
                    "streamer_name": streamer_name,
                    "platform": platform,
                    "assigned_agent": assigned_agent
                }
            )
            db.session.add(log_entry)
            db.session.commit()
            
            # Function needs to be imported or defined elsewhere
            from notifications import send_notifications
            send_notifications(log_entry)
            
            return jsonify({
                "message": "Object detection logged",
                "detections": detections
            }), 200
        
        return jsonify({"message": "No valid detection type provided"}), 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@detection_bp.route("/api/stop-detection", methods=["POST"])
def stop_detection_route():
    data = request.get_json()
    stream_url = data.get("stream_url")
    if not stream_url:
        return jsonify({"error": "Missing stream_url"}), 400
    if stream_url not in detection_threads:
        return jsonify({"message": "No detection running for this stream"}), 404
    threads, chat_thread, cancel_event = detection_threads.pop(stream_url)
    cancel_event.set()
    threads.join(timeout=5)
    chat_thread.join(timeout=5)
    return jsonify({"message": "Detection stopped"}), 200