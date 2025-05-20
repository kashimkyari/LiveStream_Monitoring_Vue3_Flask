import logging
import numpy as np
from datetime import datetime
import os
import librosa
from flask import current_app
from gevent.lock import Semaphore
from models import DetectionLog, Stream, ChaturbateStream, StripchatStream, ChatKeyword
from extensions import db
from utils.notifications import emit_notification
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# External dependencies
_whisper_model = None
_whisper_lock = Semaphore()

def initialize_audio_globals(whisper_model, whisper_lock):
    """Initialize global variables for model and lock"""
    global _whisper_model, _whisper_lock
    _whisper_model = whisper_model
    if whisper_lock is not None:
        _whisper_lock = whisper_lock
    logger.info("Audio globals initialized")

def load_whisper_model():
    """Load the OpenAI Whisper model with configurable size and fallback"""
    enable_audio_monitoring = os.getenv('ENABLE_AUDIO_MONITORING', 'true').lower() == 'true'
    if not enable_audio_monitoring:
        logger.info("Audio monitoring disabled; skipping Whisper model loading")
        return None
    global _whisper_model, _whisper_lock
    if not isinstance(_whisper_lock, Semaphore):
        logger.warning("Whisper lock not initialized; resetting to Semaphore")
        _whisper_lock = Semaphore()
    with _whisper_lock:
        if _whisper_model is None:
            try:
                import whisper
                model_size = os.getenv('WHISPER_MODEL_SIZE', 'medium')
                logger.info(f"Loading Whisper model: {model_size}")
                _whisper_model = whisper.load_model(model_size)
                logger.info(f"Whisper model '{model_size}' loaded successfully")
            except AttributeError as e:
                logger.error(f"Whisper attribute error: {e}. Ensure 'openai-whisper' is installed correctly.")
                try:
                    logger.info("Attempting to load fallback 'base' model")
                    _whisper_model = whisper.load_model("base")
                    logger.info("Fallback Whisper model loaded")
                except Exception as e2:
                    logger.error(f"Error loading fallback model: {e2}")
                    _whisper_model = None
            except Exception as e:
                logger.error(f"Error loading Whisper model: {e}")
                _whisper_model = None
    if _whisper_model is None:
        logger.warning("Whisper model unavailable; audio processing will be skipped.")
    return _whisper_model

def refresh_flagged_keywords():
    """Retrieve current flagged keywords from database"""
    with current_app.app_context():
        keywords = [kw.keyword.lower() for kw in ChatKeyword.query.all()]
    logger.debug(f"Retrieved {len(keywords)} flagged keywords")
    return keywords

def get_stream_info(stream_url):
    """Identify platform and streamer from URL"""
    with current_app.app_context():
        cb_stream = ChaturbateStream.query.filter_by(chaturbate_m3u8_url=stream_url).first()
        if cb_stream:
            return 'chaturbate', cb_stream.streamer_username
        sc_stream = StripchatStream.query.filter_by(stripchat_m3u8_url=stream_url).first()
        if sc_stream:
            return 'stripchat', sc_stream.streamer_username
        stream = Stream.query.filter_by(room_url=stream_url).first()
        if stream:
            return stream.type.lower(), stream.streamer_username
    return 'unknown', 'unknown'

def get_stream_assignment(stream_url):
    """Get assignment info for a stream"""
    from sqlalchemy.orm import joinedload
    with current_app.app_context():
        stream = Stream.query.filter_by(room_url=stream_url).first()
        if not stream:
            cb_stream = ChaturbateStream.query.filter_by(chaturbate_m3u8_url=stream_url).first()
            if cb_stream:
                stream = Stream.query.get(cb_stream.id)
            else:
                sc_stream = StripchatStream.query.filter_by(stripchat_m3u8_url=stream_url).first()
                if sc_stream:
                    stream = Stream.query.get(sc_stream.id)
        
        if not stream:
            logger.warning(f"No stream found for URL: {stream_url}")
            return None, None
        
        from models import Assignment
        query = Assignment.query.options(
            joinedload(Assignment.agent),
            joinedload(Assignment.stream)
        ).filter_by(stream_id=stream.id)
        
        assignments = query.all()
        
        if not assignments:
            logger.info(f"No assignments found for stream: {stream_url}")
            return None, None
        
        assignment = assignments[0]
        agent_id = assignment.agent_id
        return assignment.id, agent_id

def normalize_audio(audio_data):
    """Normalize audio volume to improve transcription reliability"""
    try:
        max_amplitude = np.max(np.abs(audio_data))
        if max_amplitude > 0:
            audio_data = audio_data / max_amplitude
        return audio_data
    except Exception as e:
        logger.error(f"Error normalizing audio: {e}")
        return audio_data

def process_audio_segment(audio_data, original_sample_rate, stream_url):
    """Process an audio segment for transcription and analysis with diagnostics"""
    enable_audio_monitoring = os.getenv('ENABLE_AUDIO_MONITORING', 'true').lower() == 'true'
    if not enable_audio_monitoring:
        logger.info(f"Audio monitoring disabled for {stream_url}")
        return [], ""
    model = load_whisper_model()
    if model is None:
        logger.warning(f"Skipping audio processing for {stream_url} due to unavailable Whisper model")
        return [], ""
    
    # Log audio diagnostics
    audio_duration = len(audio_data) / original_sample_rate
    audio_amplitude = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 0
    logger.info(f"Audio segment for {stream_url}: duration={audio_duration:.2f}s, sample_rate={original_sample_rate}, max_amplitude={audio_amplitude:.4f}")
    
    if audio_amplitude < 1e-5:
        logger.warning(f"Audio segment for {stream_url} has very low amplitude; may be silent")
        return [], ""
    
    try:
        target_sr = 16000
        # Normalize audio
        audio_data = normalize_audio(audio_data)
        # Resample if necessary
        if original_sample_rate != target_sr:
            audio_data = librosa.resample(audio_data, orig_sr=original_sample_rate, target_sr=target_sr)
        logger.info(f"Transcribing audio for {stream_url}")
        result = model.transcribe(audio_data, fp16=False, verbose=False)
        transcript = result.get("text", "").strip()
        if not transcript:
            logger.warning(f"Empty transcription for {stream_url}; audio may be silent or unintelligible")
        else:
            logger.info(f"Transcription for {stream_url}: {transcript[:100]}...")
        keywords = refresh_flagged_keywords()
        detected_keywords = [kw for kw in keywords if kw in transcript.lower()]
        detections = []
        if detected_keywords:
            detection = {
                "timestamp": datetime.now().isoformat(),
                "transcript": transcript,
                "keyword": detected_keywords
            }
            detections.append(detection)
        return detections, transcript
    except Exception as e:
        logger.error(f"Error processing audio for {stream_url}: {e}")
        return [], ""

def log_audio_detection(detection, stream_url):
    """Log audio detections to database"""
    enable_audio_monitoring = os.getenv('ENABLE_AUDIO_MONITORING', 'true').lower() == 'true'
    if not enable_audio_monitoring:
        return
    platform, streamer = get_stream_info(stream_url)
    assignment_id, agent_id = get_stream_assignment(stream_url)
    details = {
        "keyword": detection.get("keyword"),
        "transcript": detection.get("transcript"),
        "timestamp": detection.get("timestamp"),
        "streamer_name": streamer,
        "platform": platform,
        "assigned_agent": agent_id
    }
    with current_app.app_context():
        log_entry = DetectionLog(
            room_url=stream_url,
            event_type="audio_detection",
            details=details,
            timestamp=datetime.now(),
            assigned_agent=agent_id,
            assignment_id=assignment_id,
            read=False
        )
        db.session.add(log_entry)
        db.session.commit()
        notification_data = {
            "id": log_entry.id,
            "event_type": log_entry.event_type,
            "timestamp": log_entry.timestamp.isoformat(),
            "details": log_entry.details,
            "read": log_entry.read,
            "room_url": log_entry.room_url,
            "streamer": streamer,
            "platform": platform,
            "assigned_agent": "Unassigned" if not agent_id else "Agent"
        }
        
        # Use environment variables for alert cooldown
        audio_alert_cooldown = int(os.getenv('AUDIO_ALERT_COOLDOWN', 60))
        # Use the configured cooldown when emitting the notification
        emit_notification(notification_data, cooldown=audio_alert_cooldown)