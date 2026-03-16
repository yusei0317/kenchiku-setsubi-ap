import streamlit as st
from core.db_handler import get_notion_data

# 1. ページ設定（一番最初に書く）
st.set_page_config(page_title="建築設備士 SRS学習アプリ", layout="wide")

def main():
    st.title("🏗️ 建築設備士 合格戦略アプリ")
    st.write(f"ようこそ、後藤さん。Notionと連動して学習を管理します。")

    # 2. Notionの接続テスト
    try:
        with st.spinner("Notionデータベースに接続中..."):
            data = get_notion_data()
            if data:
                st.success("✅ Notionとの同期に成功しました！左メニューから各機能を選んでください。")
            else:
                st.warning("⚠️ Notionにデータが見つかりません。")
    except Exception as e:
        st.error(f"❌ Notionへの接続に失敗しました。")
        st.caption(f"エラー詳細: {e}")

    st.divider()
    st.write(r"排煙風量 $2\,m^3/s$ などの重要数値をマスターしましょう。")

if __name__ == "__main__":
    main()
