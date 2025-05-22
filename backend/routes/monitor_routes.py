# monitor_routes.py
from flask import Blueprint, request, jsonify, current_app
from models import Stream
from extensions import db
from monitoring import start_monitoring, stop_monitoring, stream_processors
from utils.notifications import emit_stream_update
from time import time

monitor_bp = Blueprint('monitor', __name__)

def get_stream_url(stream):
    """Get the appropriate stream URL (M3U8 or room URL) from a Stream object."""
    for attr in dir(stream):
        if attr.endswith('_m3u8_url'):
            stream_url = getattr(stream, attr, '')
            if stream_url:
                return stream_url
    return getattr(stream, 'stream_url', getattr(stream, 'room_url', ''))

@monitor_bp.route("/api/monitor/trigger-detection", methods=["POST"])
def trigger_detection():
    """Handle detection trigger requests from the main app."""
    current_app.logger.info("Received request to /api/monitor/trigger-detection")
    data = request.get_json()
    current_app.logger.info(f"Request data: {data}")
    stream_id = data.get("stream_id")
    stop = data.get("stop", False)
    current_app.logger.info(f"Stream ID: {stream_id}, Stop: {stop}")

    if not stream_id:
        return jsonify({"error": "Missing stream_id"}), 400

    stream = Stream.query.get(stream_id)
    if not stream:
        return jsonify({"error": "Stream not found"}), 404

    stream_url = get_stream_url(stream)

    if stop:
        if stream.is_monitored or stream_url in stream_processors:
            try:
                stop_monitoring(stream)
                stream.is_monitored = False
                db.session.commit()
                current_app.logger.info(f"Detection stopped for stream: {stream.id}")
                emit_stream_update({
                    'id': stream.id,
                    'url': stream_url,
                    'status': 'stopped',
                    'type': stream.type
                })
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

    if stream.status == 'offline':
        current_app.logger.info(f"Cannot start detection for offline stream: {stream.id}")
        return jsonify({
            "error": "Cannot start detection for offline stream",
            "stream_id": stream.id,
            "active": False,
            "status": stream.status or "unknown",
            "isDetecting": False,
            "isDetectionLoading": False,
            "detectionError": "Stream is offline"
        }), 400

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
        }), 409

    try:
        current_app.logger.info(f"Starting detection for stream: {stream.id}")
        if start_monitoring(stream):
            stream.is_monitored = True
            db.session.commit()
            emit_stream_update({
                'id': stream.id,
                'url': stream_url,
                'status': 'monitoring',
                'type': stream.type
            })
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

@monitor_bp.route("/api/monitor/detection-status/<int:stream_id>", methods=["GET"])
def detection_status(stream_id):
    start_time = time()
    current_app.logger.info(f"Starting detection_status for stream_id={stream_id}")
    
    stream = Stream.query.get_or_404(stream_id)
    current_app.logger.info(f"Database query took {time() - start_time:.2f} seconds")
    
    stream_url = get_stream_url(stream)
    current_app.logger.info(f"get_stream_url took {time() - start_time:.2f} seconds")
    
    is_active = (stream_url in stream_processors or stream.is_monitored) and stream.status != 'offline'
    stream_status = getattr(stream, 'status', 'unknown')
    current_app.logger.info(f"Status checks took {time() - start_time:.2f} seconds")
    
    response = {
        "stream_id": stream_id,
        "stream_url": stream_url,
        "active": is_active,
        "status": stream_status,
        "isDetecting": is_active,
        "isDetectionLoading": False,
        "detectionError": "Stream is offline" if stream.status == 'offline' else None
    }
    current_app.logger.info(f"Total time for detection_status: {time() - start_time:.2f} seconds")
    return jsonify(response)