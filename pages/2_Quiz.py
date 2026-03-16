import streamlit as st
import random
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

# --- ページ設定 ---
st.set_page_config(page_title="クイズモード", layout="wide")

# スタイル設定
st.markdown("""
<style>
    .question-box { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; margin-bottom: 15px; }
    .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; text-align: left; }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🧠 クイズモード (SRS学習)")

    # 1. データの読み込み（Notionから直接取得）
    if 'questions' not in st.session_state:
        with st.spinner("Notionから最新の問題を読み込み中..."):
            all_raw_data = get_notion_data()
            # 「今日復習すべきID」を取得
            due_ids = get_due_questions()
            
            questions = []
            for item in all_raw_data:
                props = item.get("properties", {})
                q_id = props.get("id", {}).get("title", [{}])[0].get("plain_text", "")
                
                # 復習期限が来ている、または未学習の問題だけをリストに入れる
                if q_id in due_ids or not due_ids:
                    questions.append({
                        "page_id": item.get("id"), # Notionの更新に必要
                        "q_id": q_id,
                        "question": props.get("question", {}).get("rich_text", [{}])[0].get("plain_text", ""),
                        "answer": props.get("answer", {}).get("rich_text", [{}])[0].get("plain_text", ""),
                        "interval": props.get("interval", {}).get("number", 0) or 0,
                        "ease_factor": props.get("ease_factor", {}).get("number", 2.5) or 2.5,
                        "reps": props.get("reps", {}).get("number", 0) or 0,
                        "image_url": props.get("image", {}).get("files", [{}])[0].get("file", {}).get("url", None)
                    })
            
            random.shuffle(questions)
            st.session_state.questions = questions
            st.session_state.current_index = 0
            st.session_state.show_answer = False

    if not st.session_state.questions:
        st.success("🎉 現在復習すべき問題はありません！")
        return

    q = st.session_state.questions[st.session_state.current_index]

    # 2. 問題表示
    st.caption(f"問題 {st.session_state.current_index + 1} / {len(st.session_state.questions)} (ID: {q['q_id']})")
    st.markdown(f'<div class="question-box">{q["question"]}</div>', unsafe_allow_html=True)

    if not st.session_state.show_answer:
        if st.button("答えを見る", type="primary"):
            st.session_state.show_answer = True
            st.rerun()
    else:
        # 正解と解説の表示
        st.success(f"【正解】 {q['answer']}")
        
        # PDFマッピング（IDから自動判別）
        pdf_num = q['q_id'].split('-')[0] if '-' in q['q_id'] else "不明"
        st.info(f"📚 参照資料: {pdf_num}番のPDFをご確認ください")
        
        if q['image_url']:
            with st.expander("🖼️ 図解を見る", expanded=True):
                st.image(q['image_url'])

        st.divider()
        st.markdown("##### 難易度を評価して次へ（Notionに保存されます）")
        
        # 3. SRSボタン（ここがNotion保存と連動！）
        cols = st.columns(4)
        labels = [("もう一度", 0), ("難しい", 1), ("普通", 2), ("簡単", 3)]
        
        for i, (label, val) in enumerate(labels):
            with cols[i]:
                if st.button(label, key=f"btn_{val}"):
                    # Notionを更新！
                    success = update_srs_data(
                        q['page_id'], val, q['interval'], q['ease_factor'], q['reps']
                    )
                    if success:
                        st.session_state.current_index += 1
                        st.session_state.show_answer = False
                        st.rerun()
                    else:
                        st.error("Notionの更新に失敗しました。")

if __name__ == "__main__":
    main()
