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
        
        # テキスト取得の共通関数（安全ガード付き）
        def get_t(name):
            prop = p.get(name, {})
            if not prop: return ""
            r_text = prop.get("rich_text", [])
            if not r_text: return ""
            return r_text[0].get("plain_text", "").strip()

        # 画像URL取得（NotionのFiles & Media型: image列）
        img_url = ""
        img_prop = p.get("image", {})
        if img_prop.get("type") == "files":
            files = img_prop.get("files", [])
            if files:
                img_url = files[0].get("file", {}).get("url") or files[0].get("external", {}).get("url")

        # ID（タイトル型）取得
        id_list = p.get("id", {}).get("title", [])
        qid = id_list[0].get("plain_text", "").strip() if id_list else ""
        if not qid: continue

        formatted_data.append({
            "page_id": item.get("id"),
            "q_id": qid,
            "question": get_t("question"),
            "answer": get_t("answer"),
            "choices": [get_t("choice_1"), get_t("choice_2"), get_t("choice_3"), get_t("choice_4")],
            "exps": [get_t("exp_1"), get_t("exp_2"), get_t("exp_3"), get_t("exp_4")],
            "image_url": img_url,
            "interval": p.get("interval", {}).get("number", 0) or 0,
            "ease_factor": p.get("ease_factor", {}).get("number", 2.5) or 2.5,
            "reps": p.get("reps", {}).get("number", 0) or 0
        })
    return formatted_data

def update_srs_data(page_id, quality, prev_interval, prev_ease, prev_reps):
    # SM-2 アルゴリズム
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
    # IDリストを安全に抽出
    ids = []
    for item in results:
        title_list = item.get("properties", {}).get("id", {}).get("title", [])
        if title_list:
            ids.append(title_list[0].get("plain_text", "").strip())
    return ids
