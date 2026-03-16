import streamlit as st
import random
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

st.set_page_config(page_title="建築設備士 択一クイズ", layout="wide")

def main():
    st.title("🧠 建築設備士 択一クイズ")

    # サイドバー設定
    st.sidebar.header("⚙️ 設定")
    mode = st.sidebar.radio("学習モード", ["忘却曲線モード", "全問トレーニング"])
    section_map = {"7": "7_配管とポンプ", "8": "8_ダクトと送風機", "10": "10_排煙設備"}
    selected_sections = st.sidebar.multiselect("分野選択", options=list(section_map.values()))

    # リロード管理
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
        st.warning("該当する問題がありません。")
        return

    q = st.session_state.questions[st.session_state.idx]
    st.info(f"【{mode}】 問題 {st.session_state.idx + 1} / {len(st.session_state.questions)} (ID: {q['q_id']})")
    st.subheader(q["question"])

    if not st.session_state.ans:
        choices = [c for c in q["choices"] if c]
        user_choice = st.radio("選択肢を選んでください：", choices, index=None)
        if st.button("回答を確定", type="primary"):
            if user_choice:
                st.session_state.selected = user_choice
                st.session_state.ans = True
                st.rerun()
    else:
        # 正誤判定
        # answer列に "1", "2" など数値が入っているか、テキストが入っているかで判定
        correct_idx = int(q["answer"]) - 1
        correct_text = q["choices"][correct_idx]
        
        if st.session_state.selected == correct_text:
            st.success(f"⭕ 正解！")
        else:
            st.error(f"❌ 不正解... 正解は肢{q['answer']} です。")

        # 各肢の解説を表示
        st.markdown("### 📝 各肢の解説")
        for i in range(4):
            if not q["choices"][i]: continue
            label = "✅ 正解の肢" if i == correct_idx else f"肢 {i+1}"
            with st.expander(f"{label}: {q['choices'][i][:30]}...", expanded=True):
                st.write(q["exps"][i])

        # 画像解説
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
