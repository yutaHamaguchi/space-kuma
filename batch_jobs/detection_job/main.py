import os
import random
import logging
from datetime import datetime
from google.cloud import storage
from google.cloud import firestore
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
PROJECT_ID = os.environ.get('PROJECT_ID')
BUCKET_RAW = os.environ.get('BUCKET_RAW', f'{PROJECT_ID}-raw-data')
LINE_NOTIFY_URL = os.environ.get('LINE_NOTIFY_URL')

def simple_detection(file_path):
    """
    Simple mock detection logic (no GPU/AI)
    Randomly generates detection events for testing
    """
    logger.info(f"Starting Simple Detection on: {file_path}")
    
    # Mock detection: 30% chance of detecting something
    detected = random.random() < 0.3
    
    if detected:
        # Generate random coordinates within target area
        # 北摂エリア: 135.4-135.6 E, 34.8-35.0 N
        lat = 34.8 + random.random() * 0.2
        lon = 135.4 + random.random() * 0.2
        score = 0.8 + random.random() * 0.2  # 0.8-1.0
        
        detection = {
            'timestamp': datetime.utcnow(),
            'file_path': file_path,
            'detected': True,
            'latitude': lat,
            'longitude': lon,
            'score': score,
            'area': '北摂エリア（モック）',
            'status': 'pending'
        }
        logger.info(f"DETECTION: Score {score:.2f} at ({lat:.4f}, {lon:.4f})")
    else:
        detection = {
            'timestamp': datetime.utcnow(),
            'file_path': file_path,
            'detected': False,
            'area': '北摂エリア（モック）',
            'status': 'completed'
        }
        logger.info("No detection")
    
    return detection

def save_detection(detection):
    """Save detection result to Firestore"""
    db = firestore.Client()
    timestamp_str = detection['timestamp'].strftime('%Y%m%d_%H%M%S')
    doc_ref = db.collection('detections').document(timestamp_str)
    doc_ref.set(detection)
    logger.info(f"Saved detection to Firestore: {timestamp_str}")
    return timestamp_str

def trigger_notification(detection_id):
    """Trigger LINE notification via Cloud Run service"""
    if not LINE_NOTIFY_URL:
        logger.warning("LINE_NOTIFY_URL not set, skipping notification")
        return
    
    try:
        response = requests.post(
            LINE_NOTIFY_URL,
            json={'detection_id': detection_id},
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"Notification triggered for {detection_id}")
    except Exception as e:
        logger.error(f"Failed to trigger notification: {e}")

def main():
    logger.info("Starting Detection Job...")
    
    try:
        # Get latest file from processing folder
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_RAW)
        blobs = list(bucket.list_blobs(prefix='processing/'))
        
        if not blobs:
            logger.warning("No files to process")
            return
        
        # Process the latest file
        latest_blob = max(blobs, key=lambda b: b.time_created)
        file_path = f'gs://{BUCKET_RAW}/{latest_blob.name}'
        
        # Run detection
        detection = simple_detection(file_path)
        
        # Save to Firestore
        detection_id = save_detection(detection)
        
        # Trigger notification if detected
        if detection['detected']:
            trigger_notification(detection_id)
        
        logger.info("Detection Job Completed.")
        
    except Exception as e:
        logger.error(f"ERROR: {str(e)}")
        raise

if __name__ == "__main__":
    main()
