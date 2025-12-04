import os
import json
import logging
from datetime import datetime
from google.cloud import storage
from google.cloud import firestore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
PROJECT_ID = os.environ.get('PROJECT_ID')
BUCKET_RAW = os.environ.get('BUCKET_RAW', f'{PROJECT_ID}-raw-data')
BUCKET_RESULTS = os.environ.get('BUCKET_RESULTS', f'{PROJECT_ID}-results')

def load_sample_data():
    """Load sample GeoTIFF from GCS samples folder"""
    logger.info("Starting Mock Data Ingest Job...")
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_RAW)
    
    # Check if sample exists
    sample_blob = bucket.blob('samples/sample_sar.tif')
    
    if not sample_blob.exists():
        logger.warning("Sample data not found. Creating placeholder...")
        # Create a minimal placeholder file
        sample_blob.upload_from_string(b"MOCK_SAR_DATA", content_type='image/tiff')
    
    # Copy sample to processing folder with timestamp
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    dest_blob_name = f'processing/{timestamp}_mock_sar.tif'
    
    bucket.copy_blob(sample_blob, bucket, dest_blob_name)
    logger.info(f"Copied sample data to: {dest_blob_name}")
    
    # Record ingestion in Firestore
    db = firestore.Client()
    doc_ref = db.collection('ingestions').document(timestamp)
    doc_ref.set({
        'timestamp': datetime.utcnow(),
        'source': 'mock_sample',
        'file_path': f'gs://{BUCKET_RAW}/{dest_blob_name}',
        'status': 'completed',
        'area': '北摂・丹波篠山エリア（モック）'
    })
    
    logger.info("Mock Data Ingest Job Completed.")
    return dest_blob_name

def main():
    try:
        file_path = load_sample_data()
        logger.info(f"SUCCESS: Ingested {file_path}")
    except Exception as e:
        logger.error(f"ERROR: {str(e)}")
        raise

if __name__ == "__main__":
    main()
