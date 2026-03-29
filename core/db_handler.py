import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import google.generativeai as genai

def get_headers():
    return {
        "Authorization": f"Bearer {st.secrets['notion']['notion_token']}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

def parse_notion_image_urls(img_prop):
    """
    Notionの 'image' (ファイル＆メディア)プロパティから堅牢にURLリストを抽出する
    """
    urls = []
    if not img_prop or img_prop.get("type") != "files":
        return urls
    
    files = img_prop.get("files", [])
    if not isinstance(files, list):
        return urls

    for file_info in files:
        url_val = None
        if file_info.get("type") == "file":
            f_obj = file_info.get("file")
            if f_obj:
                url_val = f_obj.get("url")
        elif file_info.get("type") == "external":
            e_obj = file_info.get("external")
            if e_obj:
                url_val = e_obj.get("url")
        
        if url_val:
            urls.append(url_val)
    return urls

@st.cache_data(ttl=300)
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
            
            def get_select(name):
                prop = p.get(name, {})
                if not prop: return ""
                select = prop.get("select")
                if select:
                    return select.get("name", "")
                return ""

            img_urls = parse_notion_image_urls(p.get("image"))

            id_list = p.get("id", {}).get("title", [])
            qid = id_list[0].get("plain_text", "").strip() if id_list else ""
            if not qid: continue

            ans_num = p.get("answer", {}).get("number")
            ans_str = str(int(ans_num)) if ans_num is not None else ""

            last_answered = p.get("last_answered", {}).get("date", {})
            last_answered_str = last_answered.get("start") if last_answered else None
            is_correct = p.get("is_correct", {}).get("checkbox", False)
            
            next_date_prop = p.get("next_date", {}).get("date", {})
            next_date_str = next_date_prop.get("start") if next_date_prop else None

            correct_count = p.get("correct_count", {}).get("number", 0) or 0
            interval = p.get("interval", {}).get("number", 0) or 0

            formatted_data.append({
                "page_id": item.get("id"),
                "q_id": qid,
                "question": get_t("question"),
                "answer": ans_str,
                "choices": [get_t("choice_1"), get_t("choice_2"), get_t("choice_3"), get_t("choice_4")],
                "exps": [get_t("exp_1"), get_t("exp_2"), get_t("exp_3"), get_t("exp_4")],
                "image_urls": img_urls,
                "interval": int(interval),
                "ease_factor": p.get("ease_factor", {}).get("number", 2.5) or 2.5,
                "reps": p.get("reps", {}).get("number", 0) or 0,
                "correct_count": int(correct_count),
                "my_memo": get_t("my_memo"),
                "last_answered": last_answered_str,
                "is_correct": is_correct,
                "next_date": next_date_str,
                "section": get_select("section"),
                "exam_info": get_t("exam_info"),
                "difficulty": get_select("difficulty"),
                "history": get_t("history") # 追記用テキストプロパティ
            })
        return formatted_data
    except Exception as e:
        st.error(f"Notionからのデータ取得に失敗しました: {e}")
        return []

def refresh_notion_images(page_id):
    try:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        res = requests.get(url, headers=get_headers())
        res.raise_for_status()
        properties = res.json().get("properties", {})
        return parse_notion_image_urls(properties.get("image"))
    except Exception as e:
        st.warning(f"画像の再取得に失敗しました: {e}")
        return []

def calculate_next_review(current_interval, is_correct):
    base_interval = current_interval if current_interval and current_interval > 0 else 1
    if is_correct:
        return max(1, round(base_interval * 2.5))
    else:
        return 1

def update_srs_data(page_id, quality, prev_interval, prev_ease, prev_reps, prev_correct_count=0, is_correct=None, prev_history=""):
    new_reps = prev_reps + 1
    new_interval = calculate_next_review(prev_interval, is_correct)
    
    if quality == 3:
        new_interval = round(new_interval * 1.2)
    elif quality <= 1:
        new_interval = 1

    today = datetime.now().strftime('%Y-%m-%d')
    next_review_date = (datetime.now() + timedelta(days=new_interval)).strftime('%Y-%m-%d')
    
    new_correct_count = prev_correct_count
    if is_correct:
        new_correct_count += 1

    # 履歴の追記ロジック: Date:Result|...
    result_char = "O" if is_correct else "X"
    new_history_entry = f"{today}:{result_char}|"
    # 容量制限を考慮し、最新の履歴を前に持ってくる、または結合
    full_history = new_history_entry + (prev_history if prev_history else "")
    # Notionのテキストプロパティ制限（2000文字程度）を考慮し、古いものをカット
    full_history = full_history[:1500]

    url = f"https://api.notion.com/v1/pages/{page_id}"
    properties = {
        "next_date": {"date": {"start": next_review_date}},
        "interval": {"number": float(new_interval)},
        "reps": {"number": int(new_reps)},
        "correct_count": {"number": int(new_correct_count)},
        "last_answered": {"date": {"start": today}},
        "is_correct": {"checkbox": bool(is_correct)},
        "history": {"rich_text": [{"text": {"content": full_history}}]}
    }
    
    payload = {"properties": properties}
    try:
        res = requests.patch(url, headers=get_headers(), json=payload)
        res.raise_for_status()
        clear_notion_cache()
        return True
    except Exception as e:
        st.error(f"Notionの更新に失敗しました: {e}")
        return False

def update_my_memo(page_id, memo_text):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {"my_memo": {"rich_text": [{"text": {"content": memo_text}}]}}
    }
    try:
        res = requests.patch(url, headers=get_headers(), json=payload)
        res.raise_for_status()
        clear_notion_cache()
        return True
    except Exception as e:
        st.error(f"Notionのメモ更新に失敗しました: {e}")
        return False

def get_stats():
    data = get_notion_data()
    if not data:
        return pd.DataFrame(), pd.DataFrame()
    
    df = pd.DataFrame(data)
    df_status = df[['q_id', 'reps', 'interval', 'last_answered', 'is_correct', 'next_date', 'section']].copy()
    df_status['mastery_level'] = df_status['reps'].apply(lambda x: 'Mastered' if x > 3 else 'Learning' if x > 0 else 'New')
    
    # 履歴プロパティから詳細なイベントを抽出
    all_logs = []
    for _, row in df.iterrows():
        hist_str = row.get("history", "")
        if not hist_str: continue
        
        # 形式: YYYY-MM-DD:Result|
        entries = hist_str.split("|")
        for entry in entries:
            if ":" in entry:
                try:
                    date_part, res_part = entry.split(":")
                    all_logs.append({
                        "timestamp": date_part,
                        "question_id": row["q_id"],
                        "section": row["section"],
                        "is_correct": True if res_part == "O" else False
                    })
                except:
                    continue
    
    df_history = pd.DataFrame(all_logs) if all_logs else pd.DataFrame(columns=['timestamp', 'question_id', 'section', 'is_correct'])
    
    return df_status, df_history

def call_gemini_api(prompt, system_instruction=""):
    api_key = st.secrets.get("gemini", {}).get("api_key")
    if not api_key: return "Gemini APIキーが設定されていません。"
    try:
        genai.configure(api_key=api_key)
        full_prompt = f"【指示・役割】\n{system_instruction}\n\n【コンテキスト】\n{prompt}" if system_instruction else prompt
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Gemini APIエラー: {e}"

def clear_notion_cache():
    import streamlit as st
    st.cache_data.clear()
