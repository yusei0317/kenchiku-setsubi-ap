import streamlit as st

# 1. 何よりも先にページ設定を行う
st.set_page_config(page_title="復旧テスト", layout="wide")

st.title("🏗️ アプリ起動テスト")
st.write("この画面が見えていれば、app.py 自体は動いています。")

try:
    from core import db_handler
    st.success("✅ core/db_handler.py の読み込みに成功しました。")
except Exception as e:
    st.error("❌ core/db_handler.py の読み込みでエラーが発生しました。")
    st.exception(e)
