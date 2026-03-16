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
        
        def get_t(name):
            prop = p.get(name, {})
            if not prop: return ""
            ptype = prop.get("type")
            if ptype == "rich_text":
                return prop.get("rich_text", [{}])[0].get("plain_text", "") if prop.get("rich_text") else ""
            elif ptype == "title":
                return prop.get("title", [{}])[0].get("plain_text", "") if prop.get("title") else ""
            return ""

        qid = get_t("id")
        if not qid: continue

        formatted_data.append({
            "page_id": item.get("id"),
            "q_id": qid,
            "question": get_t("question"),
            "answer": get_t("answer"),
            # ここを choice_1, choice_2... に修正
            "choices": [get_t("choice_1"), get_t("choice_2"), get_t("choice_3"), get_t("choice_4")],
            "image_url": p.get("image_url", {}).get("url", ""),
            "interval": p.get("interval", {}).get("number", 0) or 0,
            "ease_factor": p.get("ease_factor", {}).get("number", 2.5) or 2.5,
            "reps": p.get("reps", {}).get("number", 0) or 0
        })
    return formatted_data

# update_srs_data と get_due_questions は変更なしでOK
