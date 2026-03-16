import streamlit as st
import json
import os
import random
import requests # ←【追加】通信用の部品
from core.db_handler import update_srs, get_due_questions

st.set_page_config(page_title="クイズモード", layout="wide", initial_sidebar_state="auto")

# Stable CSS for fixes
st.markdown("""
<style>
    /* 1. Mobile Sidebar Fix */
    [data-testid="stHeader"] {
        z-index: 1000000 !important;
        background: rgba(255, 255, 255, 0.8) !important;
    }
    
    /* 2. Button and Layout Stability */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: auto;
        min-height: 3.2em;
        font-weight: bold;
        text-align: left;
        padding: 10px 15px;
        white-space: normal;
        margin-bottom: 5px;
    }
    
    .question-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin-bottom: 15px;
        min-height: 120px;
    }
    
    .answer-box {
        background-color: #e7f3ff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# === 【追加】Notionから「画像だけ」を引っ張ってくる魔法の関数 ===
@st.cache_data(ttl=600)
def get_notion_images():
    try:
        token = st.secrets["notion"]["notion_token"]
        db_id = st.secrets["notion"]["database_id"]
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers)
        results = response.json().get("results", [])
        
        image_map = {}
        for item in results:
            props = item.get("properties", {})
            title_prop = props.get("id", {}).get("title", [])
            q_id = title_prop[0].get("plain_text", "") if title_prop else ""
            
            img_url = None
            img_prop = props.get("image", {}).get("files", [])
            if img_prop:
                if img_prop[0].get("type") == "file":
                    img_url = img_prop[0].get("file", {}).get("url")
                elif img_prop[0].get("type") == "external":
                    img_url = img_prop[0].get("external", {}).get("url")
                    
            if q_id and img_url:
                image_map[q_id] = img_url
        return image_map
    except Exception as e:
        return {}
# ========================================================

def load_questions():
    with open('exam_db/questions.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    st.title("🧠 クイズモード (SRS学習)")
    
    # Initialize session state (Stable)
    if 'questions' not in st.session_state:
        all_questions = load_questions()
        due_ids = get_due_questions()
        
        if not due_ids
        
