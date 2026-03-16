import streamlit as st
import requests
from datetime import datetime, timedelta

# --- 1. Notion APIの設定 (Secretsから取得) ---
TOKEN = st.secrets["notion"]["notion_token"]
DATABASE_ID = st.secrets["notion"]["database_id"]
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def get_notion_data():
    """Notionから全問題データを取得する"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=HEADERS)
    if response.status_code != 200:
        st.error(f"データ取得エラー: {response.text}")
        return []
    return response.json().get("results", [])

def update_srs_data(page_id, quality, prev_interval, prev_ease, prev_reps):
    """
    SM-2アルゴリズムに基づき、NotionのSRSステータスを更新する
    quality: 0(もう一度), 1(難しい), 2(普通), 3(簡単)
    """
    # 1. SM-2 アルゴリズムによる計算
    # 評価が2(普通)以上の場合
    if quality >= 2:
        if prev_reps == 0:
            new_interval = 1
        elif prev_reps == 1:
            new_interval = 6
        else:
            new_interval = max(1, round(prev_interval * prev_ease))
        
        new_reps = prev_reps + 1
        # 易しさ係数の更新 (0.8〜2.5の範囲に収める)
        # 評価3なら増加、評価2なら維持または微減
        new_ease = prev_ease + (0.1 - (3 - quality) * (0.08 + (3 - quality) * 0.02))
    else:
        # 評価が0-1(難しい)の場合はリセット
        new_reps = 0
        new_interval = 1
        new_ease = max(1.3, prev_ease - 0.2)

    new_ease = max(1.3, min(2.5, new_ease)) # 下限1.3, 上限2.5に制限

    # 2. 次回の学習日を計算
    next_date = (datetime.now() + timedelta(days=new_interval)).strftime('%Y-%m-%d')

    # 3. Notionのページを更新（PATCHリクエスト）
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "next_date": {"date": {"start": next_date}},
            "interval": {"number": new_interval},
            "ease_factor": {"number": round(new_ease, 2)},
            "reps": {"number": new_reps}
        }
    }
    
    res = requests.patch(url, headers=HEADERS, json=payload)
    return res.status_code == 200

def get_due_questions():
    """今日、復習すべき期限が来ている問題のIDリストを取得する"""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    # next_dateが今日以前の問題をフィルター
    filter_data = {
        "filter": {
            "or": [
                {"property": "next_date", "date": {"on_or_before": today}},
                {"property": "next_date", "is_empty": True} # 未学習も含む
            ]
        }
    }
    
    response = requests.post(url, headers=HEADERS, json=filter_data)
    results = response.json().get("results", [])
    
    # 問題のID(Notionの「id」列)をリストにして返す
    due_ids = []
    for item in results:
        props = item.get("properties", {})
        title_prop = props.get("id", {}).get("title", [])
        if title_prop:
            due_ids.append(title_prop[0].get("plain_text"))
            
    return due_ids
