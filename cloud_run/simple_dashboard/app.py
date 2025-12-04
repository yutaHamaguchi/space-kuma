import streamlit as st
from google.cloud import firestore
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(
    page_title="Space Guardian Dashboard",
    page_icon="🛰️",
    layout="wide"
)

st.title("🛰️ Space Guardian Dashboard")
st.caption("衛星画像AI解析による緊急事態検知システム（フェーズ0: プロトタイプ）")

@st.cache_resource
def get_firestore_client():
    return firestore.Client()

def fetch_detections(hours=24):
    """Fetch detections from last N hours"""
    db = get_firestore_client()
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    detections = []
    docs = db.collection('detections').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(100).stream()
    
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        
        # Filter by time
        if data.get('timestamp') and data['timestamp'] >= cutoff_time:
            detections.append(data)
    
    return detections

# Sidebar filters
st.sidebar.header("フィルター")
time_range = st.sidebar.selectbox(
    "表示期間",
    options=[6, 12, 24, 48, 72],
    index=2,
    format_func=lambda x: f"過去{x}時間"
)

show_only_detected = st.sidebar.checkbox("検知ありのみ表示", value=True)

# Fetch data
with st.spinner("データ読み込み中..."):
    detections = fetch_detections(hours=time_range)

# Filter
if show_only_detected:
    detections = [d for d in detections if d.get('detected', False)]

# Metrics
st.header("📊 統計")
col1, col2, col3 = st.columns(3)

total_scans = len(detections) if not show_only_detected else len(fetch_detections(hours=time_range))
detected_count = len([d for d in detections if d.get('detected', False)])
pending_count = len([d for d in detections if d.get('status') == 'pending'])

col1.metric("総スキャン数", total_scans)
col2.metric("検知件数", detected_count)
col3.metric("未確認", pending_count)

# Detection list
st.header("🔍 検知ログ")

if not detections:
    st.info("表示する検知データがありません。")
else:
    for detection in detections:
        detected = detection.get('detected', False)
        
        if detected:
            with st.expander(
                f"🚨 検知 - {detection.get('area', '不明')} - {detection['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
                expanded=False
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**確度:** {detection.get('score', 0):.1%}")
                    st.write(f"**座標:** {detection.get('latitude', 0):.6f}, {detection.get('longitude', 0):.6f}")
                    st.write(f"**ステータス:** {detection.get('status', '不明')}")
                    st.write(f"**通知済み:** {'✅' if detection.get('notified') else '❌'}")
                
                with col2:
                    lat = detection.get('latitude', 0)
                    lon = detection.get('longitude', 0)
                    maps_link = f"https://www.google.com/maps?q={lat},{lon}"
                    st.link_button("📍 Google Mapsで開く", maps_link)
        else:
            with st.expander(
                f"✅ 異常なし - {detection.get('area', '不明')} - {detection['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
                expanded=False
            ):
                st.write(f"**ステータス:** {detection.get('status', '不明')}")

# Auto-refresh
st.sidebar.markdown("---")
if st.sidebar.button("🔄 更新"):
    st.rerun()

st.sidebar.caption("自動更新は未実装です。手動で更新ボタンを押してください。")
