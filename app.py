import streamlit as st
import sys

# 1. ページ設定を一番最初に実行（これが無いと白紙になりやすい）
st.set_page_config(page_title="建築設備士アプリ", layout="wide")

try:
    # 自作モジュールの読み込みを try 内で行う
    from core.db_handler import get_notion_data
except Exception as e:
    st.error("【インポートエラー】core/db_handler.py からの読み込みに失敗しました。")
    st.exception(e) # 画面にエラー詳細を表示
    st.stop()

def main():
    st.title("🏗️ 建築設備士 合格戦略アプリ")
    
    # 接続テスト
    try:
        with st.spinner("Notionに接続中..."):
            data = get_notion_data()
            if data:
                st.success("✅ Notion同期成功！左メニューから選んでください。")
            else:
                st.warning("⚠️ 接続はできましたが、データが空です。")
    except Exception as e:
        st.error("❌ Notion接続エラー！Secretsの設定を確認してください。")
        st.exception(e)

    st.divider()
    # r"..." を使うことで LaTeX の警告を回避
    st.write(r"排煙設備の風量 $2\,m^3/s$ などをマスターしましょう。")

if __name__ == "__main__":
    main()
