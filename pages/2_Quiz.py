import streamlit as st
import random
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

st.set_page_config(page_title="クイズモード", layout="wide")

def main():
    st.title("🧠 建築設備士 クイズ")

    # サイドバーでモード選択
    st.sidebar.header("学習設定")
    mode = st.sidebar.radio(
        "学習モードを選択",
        ["忘却曲線モード (推奨)", "全問トレーニング (無制限)"]
    )

    if 'questions' not in st.session_state or st.sidebar.button("問題をリロード"):
        with st.spinner("Notionからデータを同期中..."):
            all_raw = get_notion_data()
            due_ids = get_due_questions()
            
            qs = []
            for item in all_raw:
                p = item.get("properties", {})
                qid = p.get("id", {}).get("title", [{}])[0].get("plain_text", "")
                
                # モードに応じたフィルタリング
                if mode == "全問トレーニング (無制限)" or qid in due_ids:
                    qs.append({
                        "page_id": item.get("id"),
                        "q_id": qid,
                        "question": p.get("question", {}).get("rich_text", [{}])[0].get("plain_text", ""),
                        "answer": p.get("answer", {}).get("rich_text", [{}])[0].get("plain_text", ""),
                        "interval": p.get("interval", {}).get("number", 0) or 0,
                        "ease_factor": p.get("ease_factor", {}).get("number", 2.5) or 2.5,
                        "reps": p.get("reps", {}).get("number", 0) or 0
                    })
            
            random.shuffle(qs)
            st.session_state.questions = qs
            st.session_state.idx = 0
            st.session_state.ans = False

    if not st.session_state.questions:
        st.success("🎉 現在復習すべき問題はありません！「全問トレーニング」に切り替えて解くことも可能です。")
        return

    # 問題表示部分は以前と同じ
    q = st.session_state.questions[st.session_state.idx]
    st.info(f"【{mode}】 ID: {q['q_id']} | 復習 {q['reps']}回目")
    st.subheader(q["question"])

    if not st.session_state.ans:
        if st.button("正解を表示"):
            st.session_state.ans = True
            st.rerun()
    else:
        st.success(f"【正解】 {q['answer']}")
        
        # PDF自動マッピング (IDの先頭数字で判別)
        pdf_prefix = q['q_id'].split('-')[0] if '-' in q['q_id'] else ""
        pdf_map = {"10": "10_排煙設備.pdf", "8": "8_ダクトと送風機.pdf", "7": "7_配管とポンプ.pdf"}
        st.caption(f"📚 参照資料: {pdf_map.get(pdf_prefix, '関連PDF')}")

        cols = st.columns(4)
        for i, label in enumerate(["もう一度", "難しい", "普通", "簡単"]):
            if cols[i].button(label):
                update_srs_data(q['page_id'], i, q['interval'], q['ease_factor'], q['reps'])
                st.session_state.idx += 1
                st.session_state.ans = False
                st.rerun()
