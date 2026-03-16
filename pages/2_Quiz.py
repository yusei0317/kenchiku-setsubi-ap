import streamlit as st
import random
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

st.set_page_config(page_title="クイズモード", layout="wide")

def main():
    st.title("🧠 建築設備士 SRSクイズ")

    if 'questions' not in st.session_state:
        with st.spinner("Notionから復習対象を抽出中..."):
            raw = get_notion_data()
            due_ids = get_due_questions()
            qs = []
            for it in raw:
                p = it.get("properties", {})
                qid = p.get("id", {}).get("title", [{}])[0].get("plain_text", "")
                if qid in due_ids:
                    qs.append({
                        "page_id": it.get("id"), "q_id": qid,
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

    if not st.session_state.questions or st.session_state.idx >= len(st.session_state.questions):
        st.success("🎉 今日の復習はすべて完了しました！")
        return

    q = st.session_state.questions[st.session_state.idx]
    st.info(f"ID: {q['q_id']} | 復習回数: {q['reps']}回")
    st.subheader(q["question"])

    if not st.session_state.ans:
        if st.button("正解を表示"):
            st.session_state.ans = True
            st.rerun()
    else:
        st.success(f"【正解】 {q['answer']}")
        # PDF自動マッピング
        pdf_map = {"10": "10_排煙設備.pdf", "8": "8_ダクトと送風機.pdf", "7": "7_配管とポンプ.pdf"}
        ref = pdf_map.get(q['q_id'].split('-')[0], "関連資料PDF")
        st.caption(f"📚 参照資料: {ref}")

        cols = st.columns(4)
        for i, label in enumerate(["もう一度", "難しい", "普通", "簡単"]):
            if cols[i].button(label):
                update_srs_data(q['page_id'], i, q['interval'], q['ease_factor'], q['reps'])
                st.session_state.idx += 1
                st.session_state.ans = False
                st.rerun()

if __name__ == "__main__":
    main()
