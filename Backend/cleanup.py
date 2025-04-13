import os
import time
import logging
import threading
from flask import current_app

def cleanup_chat_images():
    """
    Remove chat images older than 20 seconds from the chat images folder.
    """
    chat_folder = current_app.config["CHAT_IMAGES_FOLDER"]
    now = time.time()
    for filename in os.listdir(chat_folder):
        filepath = os.path.join(chat_folder, filename)
        if os.path.isfile(filepath):
            file_age = now - os.path.getctime(filepath)
            if file_age > 20:
                try:
                    os.remove(filepath)
                except Exception as e:
                    logging.error("Error deleting file %s: %s", filepath, e)

def start_chat_cleanup_thread():
    """Start a background thread to clean up chat images."""
    def cleanup_loop():
        while True:
            try:
                # Using with statement to create application context
                from config import create_app
                app = create_app()
                with app.app_context():
                    cleanup_chat_images()
            except Exception as e:
                logging.error("Chat cleanup error: %s", e)
            time.sleep(20)
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()

def cleanup_detection_images():
    """
    Remove detection images older than 30 minutes from the detections folder.
    """
    detections_folder = "detections"
    now = time.time()
    threshold = 1800  # 30 minutes
    if not os.path.exists(detections_folder):
        return
    for filename in os.listdir(detections_folder):
        filepath = os.path.join(detections_folder, filename)
        if os.path.isfile(filepath):
            file_age = now - os.path.getctime(filepath)
            if file_age > threshold:
                try:
                    os.remove(filepath)
                except Exception as e:
                    logging.error("Error deleting detection image %s: %s", filepath, e)

def start_detection_cleanup_thread():
    """Start a background thread to clean up detection images."""
    def cleanup_loop():
        while True:
            try:
                cleanup_detection_images()
            except Exception as e:
                logging.error("Detection cleanup error: %s", e)
            time.sleep(1800)
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()