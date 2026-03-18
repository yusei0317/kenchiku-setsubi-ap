import streamlit as st
import random
from core.db_handler import get_notion_data, update_srs_data, get_due_questions, update_my_memo

st.set_page_config(page_title="建築設備士 択一クイズ", layout="wide")

# Custom CSS for Quiz and Mobile Optimization
st.markdown("""
<style>
    .choice-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
    }
    .correct-choice {
        border-left: 10px solid #28a745;
        background-color: #f8fff9;
    }
    .incorrect-choice {
        border-left: 5px solid #dc3545;
    }
    .exp-box {
        background-color: #f1f3f5;
        padding: 10px;
        border-radius: 5px;
        font-size: 0.9em;
        margin-top: 5px;
    }
    
    /* Mobile Optimization: Larger radio button targets */
    div[data-testid="stRadio"] > div {
        gap: 10px;
    }
    div[data-testid="stRadio"] label {
        background-color: white;
        padding: 15px 20px !important;
        border-radius: 12px;
        border: 1px solid #ddd;
        width: 100%;
        margin-bottom: 5px;
        transition: all 0.2s;
    }
    div[data-testid="stRadio"] label:active {
        transform: scale(0.98);
        background-color: #f0f2f6;
    }
    /* Hide the actual radio circle to make it feel like a button list */
    div[data-testid="stRadio"] input {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🧠 建築設備士 択一クイズ")

    if 'all_notion_data' not in st.session_state:
        with st.spinner("Notionからデータを読み込み中..."):
            st.session_state.all_notion_data = get_notion_data()

    if not st.session_state.all_notion_data:
        st.error("Notionからデータが取得できませんでした。設定を確認してください。")
        return

    available_sections = sorted(list(set([q['section'] for q in st.session_state.all_notion_data if q.get('section')])))

    # サイドバーはモード選択のみ残す
    st.sidebar.header("⚙️ 学習モード")
    mode = st.sidebar.radio("モード", ["忘却曲線モード", "全問トレーニング"])

    # メイン画面に分野選択を移動（解答後は自動で折りたたまれるようExpanderを使用）
    with st.expander("📂 分野・フィルター設定", expanded=not st.session_state.get('ans', False)):
        selected_sections = st.multiselect("分野を選択（空で全表示）", options=available_sections)

    cfg_key = f"{mode}-{selected_sections}"
    if "last_cfg" not in st.session_state or st.session_state.last_cfg != cfg_key:
        if "questions" in st.session_state: del st.session_state.questions
        st.session_state.last_cfg = cfg_key

    if 'questions' not in st.session_state:
        due_ids = get_due_questions()
        qs = [
            q for q in st.session_state.all_notion_data 
            if (not selected_sections or q['section'] in selected_sections) and 
               (mode == "全問トレーニング" or q['q_id'] in due_ids)
        ]
        random.shuffle(qs)
        st.session_state.questions = qs
        st.session_state.idx = 0
        st.session_state.ans = False
        st.session_state.selected = None

    if not st.session_state.questions:
        st.warning("該当する問題がありません。")
        if st.button("全問トレーニングに切り替える"):
            st.session_state.last_cfg = ""
            st.rerun()
        return

    if st.session_state.idx >= len(st.session_state.questions):
        st.balloons()
        st.success("全てのクイズが完了しました！")
        if st.button("最初から解き直す"):
            st.session_state.idx = 0
            random.shuffle(st.session_state.questions)
            st.rerun()
        return

    q = st.session_state.questions[st.session_state.idx]
    st.session_state.current_question = q

    st.info(f"【{mode}】 {st.session_state.idx + 1} / {len(st.session_state.questions)} (ID: {q['q_id']})")
    st.subheader(q["question"])

    if not st.session_state.ans:
        # 解答フェーズ
        choices = [c for c in q["choices"] if c]
        user_choice = st.radio("選択してください：", choices, index=None, key=f"q_{st.session_state.idx}")
        
        if st.button("回答を確定", type="primary", use_container_width=True):
            if user_choice:
                st.session_state.selected = user_choice
                st.session_state.ans = True
                st.rerun()
            else:
                st.warning("選択肢を選んでください。")
    else:
        # 結果フェーズ
        ans_raw = str(q["answer"]).strip()
        correct_idx = int(ans_raw) - 1 if ans_raw.isdigit() else -1
        correct_text = q["choices"][correct_idx] if correct_idx >= 0 else "不明"
        is_correct = (st.session_state.selected == correct_text)

        # 1. 各肢の詳細解説
        st.divider()
        st.markdown("### 📝 各肢の詳細解説")
        for i in range(4):
            choice_text = q["choices"][i]
            if not choice_text: continue
            exp_text = q["exps"][i] if i < len(q["exps"]) else "解説なし"
            is_this_correct = (i == correct_idx)
            is_this_selected = (st.session_state.selected == choice_text)
            
            box_style = "choice-container"
            if is_this_correct:
                box_style += " correct-choice"
                label = f"🎯 肢 {i+1} (正解)"
            elif is_this_selected:
                box_style += " incorrect-choice"
                label = f"❌ 肢 {i+1} (あなたの選択)"
            else:
                label = f"肢 {i+1}"
            
            st.markdown(f"""
            <div class="{box_style}">
                <strong>{label}</strong><br>
                {choice_text}
                <div class="exp-box">
                    <strong>解説:</strong> {exp_text}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 2. AI Tutor
        st.info("💡 解説を読んでも分からない場合は、サイドバーの「4_AI_Tutor」へ。")

        # 3. 正誤判定
        if is_correct:
            st.success(f"⭕ 正解！ (正解：肢 {ans_raw})")
        else:
            st.error(f"❌ 不正解... (正解：肢 {ans_raw})")

        # 4. 問題画像
        if q.get("image_urls"):
            for url in q["image_urls"]:
                st.divider()
                st.image(url, use_container_width=True, caption=f"【図解】{q['q_id']}")

        # 5. 思考の振り返りメモ
        st.divider()
        st.subheader("🧠 思考の振り返りメモ")
        memo_key = f"memo_{q['page_id']}"
        if memo_key not in st.session_state:
            st.session_state[memo_key] = q.get("my_memo", "")
        memo_text = st.text_area("気づきや間違えた理由をメモしましょう：", value=st.session_state[memo_key], key=f"ta_{q['page_id']}")
        if st.button("メモを保存", key=f"save_{q['page_id']}", use_container_width=True):
            with st.spinner("Notionに保存中..."):
                if update_my_memo(q['page_id'], memo_text):
                    st.session_state[memo_key] = memo_text
                    q["my_memo"] = memo_text 
                    st.toast("メモを保存しました！", icon="✅")

        # 6. SRSボタン
        st.divider()
        st.markdown("##### 復習タイミングを選択（SRS更新）")
        cols = st.columns(4)
        labels = ["もう一度", "難しい", "普通", "簡単"]
        for i, label in enumerate(labels):
            if cols[i].button(label, key=f"srs_{i}", use_container_width=True):
                with st.spinner("Notionを更新中..."):
                    update_srs_data(q['page_id'], i, q['interval'], q['ease_factor'], q['reps'], is_correct_input=is_correct)
                st.session_state.idx += 1
                st.session_state.ans = False
                st.session_state.selected = None
                memo_key = f"memo_{q['page_id']}"
                if memo_key in st.session_state:
                    del st.session_state[memo_key]
                st.rerun()

if __name__ == "__main__":
    main()
