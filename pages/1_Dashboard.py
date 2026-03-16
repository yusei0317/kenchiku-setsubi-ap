import streamlit as st
import pandas as pd
from datetime import datetime
from core.db_handler import get_notion_data

st.set_page_config(page_title="建築設備士ダッシュボード", layout="wide")

def main():
    st.title("📊 学習進捗ダッシュボード")

    # Notionから最新データを取得
    with st.spinner("データを同期中..."):
        raw_data = get_notion_data()
        
    if not raw_data:
        st.warning("Notionにデータがありません。")
        return

    # データを解析
    rows = []
    for item in raw_data:
        p = item.get("properties", {})
        rows.append({
            "interval": p.get("interval", {}).get("number", 0) or 0,
            "reps": p.get("reps", {}).get("number", 0) or 0
        })
    df = pd.DataFrame(rows)

    # 指標の計算
    total_q = len(df)
    # 復習間隔が15日以上のものを「マスター」と定義
    mastered_q = len(df[df['interval'] >= 15])
    mastery_rate = int((mastered_q / total_q) * 100) if total_q > 0 else 0

    # メトリクス表示
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("マスター率 (定着済み)", f"{mastery_rate}%")
    with col2:
        st.metric("総問題数", f"{total_q}問")
    with col3:
        st.metric("学習中", f"{total_q - mastered_q}問")

    st.progress(mastery_rate / 100)
    st.caption(f"全 {total_q} 問中、{mastered_q} 問が長期記憶に定着しています。")

    # AI弱点診断（簡易版）
    st.divider()
    st.subheader("🤖 AI弱点診断 (β)")
    if mastery_rate < 30:
        st.info("現在は基礎固めの時期です。排煙設備の数値（2 m3/sなど）を繰り返し解いて、間隔を伸ばしましょう。")
    else:
        st.success("順調です！特定の分野（10_排煙設備など）で評価「難しい」が続く場合は、PDF資料を読み直してください。")

if __name__ == "__main__":
    main()
