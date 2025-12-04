import os
import logging
from fastapi import FastAPI, Request, HTTPException
from google.cloud import firestore
import requests

app = FastAPI()
logger = logging.getLogger(__name__)

# Environment variables
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')  # Target user/group ID

def send_line_message(message: str):
    """Send message via LINE Messaging API"""
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        logger.warning("LINE credentials not configured")
        return False
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    
    payload = {
        'to': LINE_USER_ID,
        'messages': [
            {
                'type': 'text',
                'text': message
            }
        ]
    }
    
    try:
        response = requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        logger.info("LINE message sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to send LINE message: {e}")
        return False

def format_detection_message(detection: dict) -> str:
    """Format detection data into LINE message"""
    lat = detection.get('latitude', 0)
    lon = detection.get('longitude', 0)
    score = detection.get('score', 0)
    timestamp = detection.get('timestamp')
    
    # Google Maps link
    maps_link = f"https://www.google.com/maps?q={lat},{lon}"
    
    message = f"""🚨 異常検知アラート

📍 場所: {detection.get('area', '不明')}
📊 確度: {score:.1%}
🕐 検知時刻: {timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else '不明'}

座標: {lat:.6f}, {lon:.6f}
地図: {maps_link}

⚠️ 現場確認をお願いします"""
    
    return message

@app.post("/notify")
async def notify(request: Request):
    """Receive detection notification request and send LINE message"""
    try:
        body = await request.json()
        detection_id = body.get('detection_id')
        
        if not detection_id:
            raise HTTPException(status_code=400, detail="detection_id required")
        
        # Fetch detection from Firestore
        db = firestore.Client()
        doc = db.collection('detections').document(detection_id).get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Detection not found")
        
        detection = doc.to_dict()
        
        # Send LINE notification
        message = format_detection_message(detection)
        success = send_line_message(message)
        
        if success:
            # Update status
            db.collection('detections').document(detection_id).update({
                'notified': True
            })
        
        return {"status": "ok", "notified": success}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in notify endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "ok", "service": "line-bot"}

@app.get("/health")
def health():
    return {"status": "healthy"}
