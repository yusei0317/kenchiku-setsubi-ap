import streamlit as st
import pandas as pd
from core.db_handler import get_notion_data

st.set_page_config(page_title="学習履歴", layout="wide")

def main():
    st.title("📜 学習履歴・定着状況")
    
    raw_data = get_notion_data()
    rows = []
    for item in raw_data:
        p = item.get("properties", {})
        rows.append({
            "問題ID": p.get("id", {}).get("title", [{}])[0].get("plain_text", ""),
            "次回学習日": p.get("next_date", {}).get("date", {}).get("start", "未学習"),
            "復習間隔(日)": p.get("interval", {}).get("number", 0),
            "回数": p.get("reps", {}).get("number", 0),
            "難易度係数": p.get("ease_factor", {}).get("number", 0)
        })
    
    df = pd.DataFrame(rows)
    st.dataframe(df.sort_values("次回学習日"), use_container_width=True)

if __name__ == "__main__":
    main()
