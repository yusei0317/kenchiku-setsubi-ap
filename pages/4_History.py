import streamlit as st
import pandas as pd
from core.db_handler import get_notion_data

# ページ設定
st.set_page_config(page_title="学習履歴", layout="wide")

def main():
    st.title("📜 学習履歴・定着ステータス")
    st.caption("Notionに保存された最新の記憶データを確認します。")

    with st.spinner("Notionから同期中..."):
        try:
            raw_data = get_notion_data()
            if not raw_data:
                st.warning("Notionにデータが見つかりません。")
                return

            # NotionのデータをPandasの表（DataFrame）に変換
            rows = []
            for item in raw_data:
                p = item.get("properties", {})
                
                # 各列のデータを安全に取得
                q_id = p.get("id", {}).get("title", [{}])[0].get("plain_text", "No ID")
                next_date = p.get("next_date", {}).get("date", {}).get("start", "未学習")
                interval = p.get("interval", {}).get("number", 0) or 0
                reps = p.get("reps", {}).get("number", 0) or 0
                ease = p.get("ease_factor", {}).get("number", 2.5) or 2.5
                
                rows.append({
                    "問題ID": q_id,
                    "次回学習予定日": next_date,
                    "復習間隔(日)": interval,
                    "正解回数": reps,
                    "易しさ係数": ease
                })
            
            df = pd.DataFrame(rows)

            # 1. 概要メトリクス
            mastered_count = len(df[df["復習間隔(日)"] >= 15])
            st.write(f"### 現在のマスター状況: {mastered_count} / {len(df)} 問")

            # 2. 詳細テーブル表示（次回学習日が近い順にソート）
            st.subheader("📋 問題別詳細データ")
            df_sorted = df.sort_values(by="次回学習予定日", ascending=True)
            
            # 見やすく色付け
            def highlight_mastered(val):
                color = '#e8f5e9' if val >= 15 else 'white'
                return f'background-color: {color}'

            st.dataframe(
                df_sorted.style.applymap(highlight_mastered, subset=["復習間隔(日)"]),
                use_container_width=True
            )

        except Exception as e:
            st.error(f"エラーが発生しました。SecretsやNotionの列名を確認してください: {e}")

if __name__ == "__main__":
    main()
