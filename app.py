import streamlit as st
from core.db_handler import get_notion_data

st.set_page_config(page_title="建築設備士 SRS学習アプリ", layout="wide")

def main():
    st.title("🏗️ 建築設備士 合格戦略アプリ")
    st.write(f"ようこそ、後藤さん。現在は2026年3月です。試験合格に向けてNotionと連動して学習を管理します。")

    # Notionの接続確認
    try:
        with st.spinner("Notionデータベースに接続中..."):
            data = get_notion_data()
            if data:
                st.success("✅ Notionとの同期に成功しました！")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info("👈 左のメニューから「Dashboard」を選んで進捗を確認してください。")
                with col2:
                    st.info("👈 「Quiz」または「Flashcard」で学習を開始してください。")
            else:
                st.warning("⚠️ Notionにデータが見つかりません。データベースに問題が登録されているか確認してください。")
    except Exception as e:
        st.error(f"❌ Notionへの接続に失敗しました。Secrets設定を確認してください。")
        st.caption(f"エラー詳細: {e}")

    st.divider()
    st.subheader("💡 今日の学習アドバイス")
    st.write("「排煙設備の風量 $2\,m^3/s$」などの数値は、忘却曲線モードで繰り返し解くのが最も効率的です。")

if __name__ == "__main__":
    main()
