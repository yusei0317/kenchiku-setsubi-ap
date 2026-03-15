import streamlit as st
from core.db_handler import init_db, get_master_data

st.set_page_config(page_title="建築設備士学習アプリ", layout="wide")

# Initialize database
init_db()

def main():
    st.title("🏗️ 建築設備士学習アプリ")
    st.markdown("""
    建築設備士の試験対策を効率化するためのアプリです。
    
    ### 🚀 主な機能
    - **ダッシュボード**: 学習進捗と苦手分野を可視化。
    - **クイズモード**: SRS（間隔反復）に基づいた効率的な復習。
    - **フラッシュカード**: 隙間時間のクイック学習。
    
    ### 📝 はじめに
    左のサイドバーからメニューを選択してください。
    """)
    
    # Load and check data
    df = get_master_data()
    if df.empty:
        st.warning("⚠️ `exam_db/1-7_haikantoponpu.csv` が見つからないか、空です。データを配置してください。")
    else:
        st.info(f"✅ 現在 {len(df)} 問のデータが読み込まれています。")

    st.sidebar.success("メニューを選択してください。")

if __name__ == "__main__":
    main()
