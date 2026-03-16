import streamlit as st
import requests
from datetime import datetime, timedelta

def get_headers():
    return {
        "Authorization": f"Bearer {st.secrets['notion']['notion_token']}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

def get_notion_data():
    db_id = st.secrets["notion"]["database_id"]
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    res = requests.post(url, headers=get_headers())
    results = res.json().get("results", [])
    
    formatted_data = []
    for item in results:
        p = item.get("properties", {})
        # タイトル（ID）
        id_prop = p.get("id", {}).get("title", [])
        qid = id_prop[0].get("plain_text", "") if id_prop else ""
        if not qid: continue

        # 各プロパティの安全な取得
        def get_text(prop_name):
            text_list = p.get(prop_name, {}).get("rich_text", [])
            return text_list[0].get("plain_text", "") if text_list else ""

        formatted_data.append({
            "page_id": item.get("id"),
            "q_id": qid,
            "question": get_text("question"),
            "answer": get_text("answer"),
            "choices": [get_text("choice1"), get_text("choice2"), get_text("choice3"), get_text("choice4")],
            "image_url": p.get("image_url", {}).get("url", ""),
            "interval": p.get("interval", {}).get("number", 0) or 0,
            "ease_factor": p.get("ease_factor", {}).get("number", 2.5) or 2.5,
            "reps": p.get("reps", {}).get("number", 0) or 0
        })
    return formatted_data

def update_srs_data(page_id, quality, prev_interval, prev_ease, prev_reps):
    if quality >= 2: # 普通・簡単
        if prev_reps == 0: new_interval = 1
        elif prev_reps == 1: new_interval = 6
        else: new_interval = max(1, round(prev_interval * prev_ease))
        new_reps = prev_reps + 1
        new_ease = prev_ease + (0.1 - (3 - quality) * (0.08 + (3 - quality) * 0.02))
    else: # もう一度・難しい
        new_reps = 0
        new_interval = 1
        new_ease = max(1.3, prev_ease - 0.2)
    
    new_ease = max(1.3, min(2.5, new_ease))
    next_date = (datetime.now() + timedelta(days=new_interval)).strftime('%Y-%m-%d')
    
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"properties": {"next_date": {"date": {"start": next_date}}, "interval": {"number": float(new_interval)}, "ease_factor": {"number": round(float(new_ease), 2)}, "reps": {"number": int(new_reps)}}}
    requests.patch(url, headers=get_headers(), json=payload)
    return True

def get_due_questions():
    db_id = st.secrets["notion"]["database_id"]
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    filter_data = {"filter": {"or": [{"property": "next_date", "date": {"on_or_before": today}}, {"property": "next_date", "is_empty": True}]}}
    res = requests.post(url, headers=get_headers(), json=filter_data)
    results = res.json().get("results", [])
    return [item.get("properties", {}).get("id", {}).get("title", [{}])[0].get("plain_text") for item in results]
