import streamlit as st
import random
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

st.set_page_config(page_title="建築設備士 択一クイズ", layout="wide")

def main():
    st.title("🧠 建築設備士 択一クイズ")

    # サイドバー
    st.sidebar.header("⚙️ 設定")
    mode = st.sidebar.radio("モード", ["忘却曲線モード", "全問トレーニング"])
    section_map = {"配管ポンプ": "7_配管とポンプ", "ダクト": "8_ダクトと送風機", "排煙": "10_排煙設備"}
    selected_sections = st.sidebar.multiselect("分野", options=list(section_map.values()))

    # リセット処理
    curr_cfg = f"{mode}-{selected_sections}"
    if "last_cfg" not in st.session_state or st.session_state.last_cfg != curr_cfg:
        if "questions" in st.session_state: del st.session_state.questions
        st.session_state.last_cfg = curr_cfg

    if 'questions' not in st.session_state:
        with st.spinner("同期中..."):
            all_data = get_notion_data()
            due_ids = get_due_questions()
            qs = [q for q in all_data if (not selected_sections or section_map.get(q['q_id'].split('_')[0]) in selected_sections) and (mode == "全問トレーニング" or q['q_id'] in due_ids)]
            random.shuffle(qs)
            st.session_state.questions = qs
            st.session_state.idx = 0
            st.session_state.ans = False

    if not st.session_state.questions:
        st.warning("問題がありません。")
        return

    q = st.session_state.questions[st.session_state.idx]
    st.info(f"【{mode}】 {st.session_state.idx + 1} / {len(st.session_state.questions)} (ID: {q['q_id']})")
    st.subheader(q["question"])

    if not st.session_state.ans:
        choices = [c for c in q["choices"] if c]
        user_choice = st.radio("選択してください：", choices, index=None)
        if st.button("回答を確定", type="primary"):
            if user_choice:
                st.session_state.selected = user_choice
                st.session_state.ans = True
                st.rerun()
    else:
        # 結果判定
        ans_raw = str(q["answer"]).strip()
        correct_idx = int(ans_raw) - 1 if ans_raw.isdigit() else -1
        correct_text = q["choices"][correct_idx] if correct_idx >= 0 else "設定エラー"

        if st.session_state.selected == correct_text:
            st.success(f"⭕ 正解！ 正解は「肢 {ans_raw}」です。")
        else:
            st.error(f"❌ 不正解... 正解は「肢 {ans_raw}」でした。")
        
        # --- 画像を最優先で大きく表示 ---
        if q["image_url"]:
            st.image(q["image_url"], use_container_width=True, caption=f"【解説図解】 {q['q_id']}")

        # --- 解説：折りたたまず全て表示 ---
        st.divider()
        st.markdown("### 📝 各肢の根拠と詳細解説")
        for i in range(4):
            if not q["choices"][i]: continue
            
            label = f"【肢 {i+1}】"
            is_target = (i == correct_idx)
            
            # 正解（不適当な肢）を強調
            if is_target:
                st.markdown(f"#### 🎯 {label} (正解)")
            else:
                st.markdown(f"#### {label}")
            
            st.write(f"**記述:** {q['choices'][i]}")
            st.info(f"**解説:** {q['exps'][i]}")
            st.divider()

        # SRSボタン
        cols = st.columns(4)
        for i, label in enumerate(["もう一度", "難しい", "普通", "簡単"]):
            if cols[i].button(label, key=f"srs_{i}"):
                update_srs_data(q['page_id'], i, q['interval'], q['ease_factor'], q['reps'])
                st.session_state.idx += 1
                st.session_state.ans = False
                st.rerun()

if __name__ == "__main__":
    main()
