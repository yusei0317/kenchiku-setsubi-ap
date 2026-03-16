import streamlit as st
import random
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

st.set_page_config(page_title="建築設備士クイズ", layout="wide")

def main():
    st.title("🧠 建築設備士 択一クイズ")

    # サイドバー設定
    st.sidebar.header("⚙️ 設定")
    mode = st.sidebar.radio("学習モード", ["忘却曲線モード", "全問トレーニング"])
    section_map = {"7": "7_配管とポンプ", "8": "8_ダクトと送風機", "10": "10_排煙設備"}
    selected_sections = st.sidebar.multiselect("分野選択", options=list(section_map.values()))

    # 設定変更でリロード
    current_cfg = f"{mode}-{selected_sections}"
    if "last_cfg" not in st.session_state or st.session_state.last_cfg != current_cfg:
        if "questions" in st.session_state: del st.session_state.questions
        st.session_state.last_cfg = current_cfg

    if 'questions' not in st.session_state:
        all_data = get_notion_data()
        due_ids = get_due_questions()
        qs = [q for q in all_data if (not selected_sections or section_map.get(q['q_id'].split('-')[0]) in selected_sections) and (mode == "全問トレーニング" or q['q_id'] in due_ids)]
        random.shuffle(qs)
        st.session_state.questions = qs
        st.session_state.idx = 0
        st.session_state.ans = False

    if not st.session_state.questions:
        st.warning("対象の問題がありません。")
        return

    q = st.session_state.questions[st.session_state.idx]
    st.info(f"【{mode}】 問題 {st.session_state.idx + 1} / {len(st.session_state.questions)} (ID: {q['q_id']})")
    st.subheader(q["question"])

    if not st.session_state.ans:
        choices = [c for c in q["choices"] if c]
        if not choices:
            st.error("選択肢(choice_1~4)の読み込みに失敗しました。Notionの列名を確認してください。")
            return
            
        user_choice = st.radio("選択肢を選んでください：", choices, index=None)
        if st.button("回答を確定", type="primary"):
            if user_choice:
                st.session_state.selected = user_choice
                st.session_state.ans = True
                st.rerun()
    else:
        # 正解判定
        if st.session_state.selected == q["answer"]:
            st.success(f"⭕ 正解！：{q['answer']}")
        else:
            st.error(f"❌ 不正解... 正解は：{q['answer']}")
        
        # --- 画像解説を表示 ---
        if q["image_url"]:
            st.image(q["image_url"], caption="図解・解説画像")
        
        st.divider()
        st.write("忘却曲線の評価（SRS）を選択してください：")
        cols = st.columns(4)
        for i, label in enumerate(["もう一度", "難しい", "普通", "簡単"]):
            if cols[i].button(label):
                update_srs_data(q['page_id'], i, q['interval'], q['ease_factor'], q['reps'])
                st.session_state.idx += 1
                st.session_state.ans = False
                st.rerun()

if __name__ == "__main__":
    main()
