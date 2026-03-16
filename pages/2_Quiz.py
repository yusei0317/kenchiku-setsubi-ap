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

    # 設定変更検知
    current_cfg = f"{mode}-{selected_sections}"
    if "last_cfg" not in st.session_state or st.session_state.last_cfg != current_cfg:
        if "questions" in st.session_state: del st.session_state.questions
        st.session_state.last_cfg = current_cfg

    if 'questions' not in st.session_state:
        with st.spinner("Notionから取得中..."):
            all_data = get_notion_data()
            due_ids = get_due_questions()
            
            qs = []
            for q in all_data:
                prefix = q['q_id'].split('-')[0]
                if selected_sections and section_map.get(prefix) not in selected_sections: continue
                if mode == "忘却曲線モード" and q['q_id'] not in due_ids: continue
                qs.append(q)
            
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

    # 回答前
    if not st.session_state.ans:
        # 4択ボタン（空文字を除外して表示）
        valid_choices = [c for c in q["choices"] if c]
        selected = st.radio("選択肢を選んでください：", valid_choices, index=None)
        
        if st.button("回答を確定", type="primary"):
            if selected:
                st.session_state.user_choice = selected
                st.session_state.ans = True
                st.rerun()
    # 回答後
    else:
        is_correct = (st.session_state.user_choice == q["answer"])
        if is_correct:
            st.success(f"⭕ 正解！：{q['answer']}")
        else:
            st.error(f"❌ 不正解... 正解は：{q['answer']}")
            st.write(f"あなたの回答：{st.session_state.user_choice}")

        # 画像の表示
        if q["image_url"]:
            st.image(q["image_url"], caption="解説図解")

        st.divider()
        st.write("今回の手応え（忘却曲線データを更新）：")
        cols = st.columns(4)
        labels = ["もう一度", "難しい", "普通", "簡単"]
        for i, label in enumerate(labels):
            if cols[i].button(label):
                update_srs_data(q['page_id'], i, q['interval'], q['ease_factor'], q['reps'])
                st.session_state.idx += 1
                st.session_state.ans = False
                st.rerun()

if __name__ == "__main__":
    main()
