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
    return res.json().get("results", [])

def update_srs_data(page_id, quality, prev_interval, prev_ease, prev_reps):
    # SM-2 logic
    if quality >= 2:
        if prev_reps == 0: new_interval = 1
        elif prev_reps == 1: new_interval = 6
        else: new_interval = max(1, round(prev_interval * prev_ease))
        new_reps = prev_reps + 1
        new_ease = prev_ease + (0.1 - (3 - quality) * (0.08 + (3 - quality) * 0.02))
    else:
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
