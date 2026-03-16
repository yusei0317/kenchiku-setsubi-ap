import streamlit as st
import requests

# --- 1. アプリの基本設定 ---
st.set_page_config(page_title="学習アプリ：空調設備", layout="centered")

# --- 2. Notionからデータを自動取得する魔法の関数 ---
@st.cache_data(ttl=600) # 10分間データを記憶して動作を軽くする
def get_notion_data():
    # 金庫(Secrets)から鍵を取り出す
    token = st.secrets["notion"]["notion_token"]
    db_id = st.secrets["notion"]["database_id"]
    
    # Notionの裏口（API）を叩く
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # 空のリクエストを送ってデータを取得
    response = requests.post(url, headers=headers)
    if response.status_code != 200:
        st.error("データの取得に失敗しました。Secretsの鍵が正しいか確認してください。")
        return []
    
    return response.json().get("results", [])

# --- 3. 画面の作成 ---
st.title("学習アプリ：空調設備")
st.info("💡 問題の追加や画像の変更は、すべてNotionから行えます！")

# Notionから問題データを引っ張ってくる
data = get_notion_data()

# データの中身を順番に画面に出す
for item in data:
    props = item.get("properties", {})
    
    # ① 問題番号（Notionの「id」列から取得）
    title_prop = props.get("id", {}).get("title", [])
    q_id = title_prop[0].get("plain_text", "無題") if title_prop else "無題"
    
    # ② 問題文（Notionの「question」列から取得）
    text_prop = props.get("question", {}).get("rich_text", [])
    q_text = text_prop[0].get("plain_text", "") if text_prop else ""
    
    # ③ 画像（Notionの「image」列から取得）
    img_url = None
    # ※もしNotion側の画像列の名前を「image」以外（例：「画像」など）にしている場合は、下の "image" を書き換えてください。
    img_prop = props.get("image", {}).get("files", [])
    if img_prop:
        if img_prop[0].get("type") == "file":
            img_url = img_prop[0].get("file", {}).get("url")
        elif img_prop[0].get("type") == "external":
            img_url = img_prop[0].get("external", {}).get("url")

    # --- ここから画面へのレイアウト ---
    st.write("---")
    st.subheader(f"■ {q_id}")
    st.write(q_text)
    
    # 画像がNotionに入っている問題だけ、図解ボタンを表示する
    if img_url:
        with st.expander("図解を見る"):
            st.image(img_url, use_container_width=True)
