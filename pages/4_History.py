import streamlit as st
import pandas as pd
from core.db_handler import get_notion_data

# ページ設定
st.set_page_config(page_title="学習履歴", layout="wide")

def main():
    st.title("📜 学習履歴・定着ステータス")
    st.caption("Notionに保存された最新の記憶データを可視化します。")

    with st.spinner("Notionからデータを取得中..."):
        try:
            raw_data = get_notion_data()
            if not raw_data:
                st.warning("Notionにデータが見つかりません。")
                return

            rows = []
            for item in raw_data:
                # ページ全体のプロパティを取得
                p = item.get("properties")
                if not p:
                    continue
                
                # --- 安全なデータ取得（ガード節） ---
                
                # 1. IDの取得
                id_prop = p.get("id", {}).get("title", [])
                q_id = id_prop[0].get("plain_text", "No ID") if id_prop else "No ID"
                
                # 2. 次回学習日の取得（ここがエラーの原因でした）
                next_date_prop = p.get("next_date", {})
                # .get("date") が None を返す場合があるため、明示的にチェック
                date_content = next_date_prop.get("date") if next_date_prop else None
                next_date = date_content.get("start") if date_content else "未学習"
                
                # 3. 数値データの取得（Noneの場合は0や初期値を設定）
                interval = p.get("interval", {}).get("number")
                if interval is None: interval = 0
                
                reps = p.get("reps", {}).get("number")
                if reps is None: reps = 0
                
                ease = p.get("ease_factor", {}).get("number")
                if ease is None: ease = 2.5

                rows.append({
                    "問題ID": q_id,
                    "次回学習予定日": next_date,
                    "定着間隔(日)": int(interval),
                    "正解回数": int(reps),
                    "易しさ": round(float(ease), 2)
                })
            
            df = pd.DataFrame(rows)

            # 統計表示
            mastered = len(df[df["定着間隔(日)"] >= 15])
            st.write(f"### 現在のマスター状況: {mastered} / {len(df)} 問")

            # テーブル表示（次回学習日が近い順、かつ未学習を下に）
            st.subheader("📋 詳細ステータス")
            df_sorted = df.sort_values(by="次回学習予定日", ascending=True)
            
            # 15日以上を緑色にするスタイル設定
            def color_interval(val):
                color = '#e8f5e9' if val >= 15 else 'white'
                return f'background-color: {color}'

            st.dataframe(
                df_sorted.style.applymap(color_interval, subset=["定着間隔(日)"]),
                use_container_width=True
            )

        except Exception as e:
            st.error(f"予期せぬエラーが発生しました: {e}")
            st.info("ヒント: Notionの各列（next_date等）が正しく作成されているか確認してください。")

if __name__ == "__main__":
    main()
