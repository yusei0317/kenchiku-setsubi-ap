import streamlit as st
import random
# db_handler から必要な関数を正確にインポート
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

st.set_page_config(page_title="建築設備士 択一クイズ", layout="wide")

def main():
    st.title("🧠 建築設備士 択一クイズ")

    # サイドバー設定
    st.sidebar.header("⚙️ 学習設定")
    mode = st.sidebar.radio("学習モード", ["忘却曲線モード", "全問トレーニング"])
    section_map = {"配管ポンプ": "7_配管とポンプ", "ダクト": "8_ダクトと送風機", "排煙": "10_排煙設備"}
    selected_sections = st.sidebar.multiselect("分野を選択", options=list(section_map.values()))

    # 設定変更でリロード
    current_cfg = f"{mode}-{selected_sections}"
    if "last_cfg" not in st.session_state or st.session_state.last_cfg != current_cfg:
        if "questions" in st.session_state:
            del st.session_state.questions
        st.session_state.last_cfg = current_cfg

    if 'questions' not in st.session_state:
        with st.spinner("Notionから最新データを取得中..."):
            all_data = get_notion_data()
            due_ids = get_due_questions()
            qs = [q for q in all_data if (not selected_sections or section_map.get(q['q_id'].split('_')[0]) in selected_sections) and (mode == "全問トレーニング" or q['q_id'] in due_ids)]
            random.shuffle(qs)
            st.session_state.questions = qs
            st.session_state.idx = 0
            st.session_state.ans = False

    if not st.session_state.questions:
        st.warning("該当する問題がありません。設定を確認してください。")
        return

    q = st.session_state.questions[st.session_state.idx]
    st.info(f"【{mode}】 問題 {st.session_state.idx + 1} / {len(st.session_state.questions)} (ID: {q['q_id']})")
    st.subheader(q["question"])

    if not st.session_state.ans:
        choices = [c for c in q["choices"] if c]
        if not choices:
            st.error("選択肢が見つかりません。Notionの列名を確認してください。")
            return
            
        user_choice = st.radio("選択肢を選んでください：", choices, index=None)
        if st.button("回答を確定", type="primary"):
            if user_choice:
                st.session_state.selected = user_choice
                st.session_state.ans = True
                st.rerun()
    else:
        # 正解番号の安全な取得
        ans_raw = str(q["answer"]).strip()
        correct_idx = int(ans_raw) - 1 if ans_raw.isdigit() else -1
        
        if correct_idx >= 0 and st.session_state.selected == q["choices"][correct_idx]:
            st.success(f"⭕ 正解！ (正解：肢 {ans_raw})")
        else:
            st.error(f"❌ 不正解... (正解：肢 {ans_raw})")

        # 全肢の解説表示
        st.markdown("### 📝 各肢の解説")
        for i in range(4):
            if not q["choices"][i]: continue
            label = f"肢 {i+1}"
            if i == correct_idx: label = f"🎯 {label} (不適当/適当)"
            with st.expander(label, expanded=(i == correct_idx)):
                st.write(f"**内容:** {q['choices'][i]}")
                st.write(f"**解説:** {q['exps'][i]}")

        if q["image_url"]:
            st.image(q["image_url"], caption="解説図解")
        
        st.divider()
        st.write("暗記度の評価：")
        cols = st.columns(4)
        for i, label in enumerate(["もう一度", "難しい", "普通", "簡単"]):
            if cols[i].button(label, key=f"srs_{i}"):
                update_srs_data(q['page_id'], i, q['interval'], q['ease_factor'], q['reps'])
                st.session_state.idx += 1
                st.session_state.ans = False
                st.rerun()

if __name__ == "__main__":
    main()
