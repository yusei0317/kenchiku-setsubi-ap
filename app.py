import streamlit as st
from core.db_handler import get_notion_data

# 1. ページ設定を最初に行う
st.set_page_config(page_title="建築設備士 SRS学習アプリ", layout="wide")

def main():
    st.title("🏗️ 建築設備士 合格戦略アプリ")
    st.write(f"ようこそ、後藤さん。2026年3月の試験合格に向けてNotionと連動して学習を管理します。")

    # 2. Notionの接続確認
    try:
        with st.spinner("Notionデータベースに接続中..."):
            data = get_notion_data()
            if data:
                st.success("✅ Notionとの同期に成功しました！")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info("👈 左のメニューから「Dashboard」を選択してください。")
                with col2:
                    st.info("👈 学習を始めるには「Quiz」を選択してください。")
            else:
                st.warning("⚠️ Notionにデータが見つかりません。")
    except Exception as e:
        st.error(f"❌ Notionへの接続に失敗しました。Secretsを確認してください。")
        st.caption(f"エラー詳細: {e}")

    st.divider()
    st.subheader("💡 今日の学習アドバイス")
    # r"..." を付けることで $2\,m^3/s$ の文法エラーを回避
    st.write(r"「排煙設備の風量 $2\,m^3/s$」などの数値は、忘却曲線モードで繰り返し解くのが最も効率的です。")

if __name__ == "__main__":
    main()
