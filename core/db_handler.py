import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

def get_headers():
    return {
        "Authorization": f"Bearer {st.secrets['notion']['notion_token']}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

@st.cache_data(ttl=600)
def get_notion_data():
    try:
        db_id = st.secrets["notion"]["database_id"]
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        res = requests.post(url, headers=get_headers())
        res.raise_for_status()
        results = res.json().get("results", [])
        
        formatted_data = []
        for item in results:
            p = item.get("properties", {})
            
            def get_t(name):
                prop = p.get(name, {})
                if not prop: return ""
                r_text = prop.get("rich_text", [])
                if r_text:
                    return r_text[0].get("plain_text", "").strip()
                return ""

            # 画像URL取得（列名: image）
            img_url = ""
            img_prop = p.get("image", {})
            if img_prop and img_prop.get("type") == "files":
                files = img_prop.get("files", [])
                if files:
                    file_info = files[0]
                    img_url = file_info.get("file", {}).get("url") or file_info.get("external", {}).get("url")

            # ID（タイトル型）
            id_list = p.get("id", {}).get("title", [])
            qid = id_list[0].get("plain_text", "").strip() if id_list else ""
            if not qid: continue

            # answerを数値型として取得し文字列に変換
            ans_num = p.get("answer", {}).get("number")
            ans_str = str(int(ans_num)) if ans_num is not None else ""

            formatted_data.append({
                "page_id": item.get("id"),
                "q_id": qid,
                "question": get_t("question"),
                "answer": ans_str,
                "choices": [get_t("choice_1"), get_t("choice_2"), get_t("choice_3"), get_t("choice_4")],
                "exps": [get_t("exp_1"), get_t("exp_2"), get_t("exp_3"), get_t("exp_4")],
                "image_url": img_url,
                "interval": p.get("interval", {}).get("number", 0) or 0,
                "ease_factor": p.get("ease_factor", {}).get("number", 2.5) or 2.5,
                "reps": p.get("reps", {}).get("number", 0) or 0
            })
        return formatted_data
    except Exception as e:
        st.error(f"Notionからのデータ取得に失敗しました: {e}")
        return []

def update_srs_data(page_id, quality, prev_interval, prev_ease, prev_reps):
    # quality: 0: 再、1: 難しい、2: 普通、3: 簡単
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
    payload = {
        "properties": {
            "next_date": {"date": {"start": next_date}},
            "interval": {"number": float(new_interval)},
            "ease_factor": {"number": round(float(new_ease), 2)},
            "reps": {"number": int(new_reps)}
        }
    }
    try:
        res = requests.patch(url, headers=get_headers(), json=payload)
        res.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Notionの更新に失敗しました: {e}")
        return False

# 互換性用のシンプルなSRS更新関数
def update_srs(qid, quality):
    data = get_notion_data()
    q = next((item for item in data if item["q_id"] == qid), None)
    if q:
        return update_srs_data(q['page_id'], quality, q['interval'], q['ease_factor'], q['reps'])
    return False

def get_due_questions():
    try:
        db_id = st.secrets["notion"]["database_id"]
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        filter_data = {
            "filter": {
                "or": [
                    {"property": "next_date", "date": {"on_or_before": today}},
                    {"property": "next_date", "is_empty": True}
                ]
            }
        }
        res = requests.post(url, headers=get_headers(), json=filter_data)
        res.raise_for_status()
        results = res.json().get("results", [])
        ids = []
        for item in results:
            title_list = item.get("properties", {}).get("id", {}).get("title", [])
            if title_list:
                ids.append(title_list[0].get("plain_text", "").strip())
        return ids
    except:
        return []

# Dashboard用の互換性関数
def get_master_data():
    data = get_notion_data()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.rename(columns={"q_id": "id"})
    return df

def get_stats():
    data = get_notion_data()
    if not data:
        return pd.DataFrame(), pd.DataFrame()
    
    df = pd.DataFrame(data)
    df_status = df[['q_id', 'reps', 'interval']].copy()
    df_status['mastery_level'] = df_status['reps'].apply(lambda x: 'Mastered' if x > 3 else 'Learning' if x > 0 else 'New')
    df_history = pd.DataFrame(columns=['question_id', 'is_correct', 'timestamp'])
    return df_status, df_history
