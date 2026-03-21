import streamlit as st
import random
import re
from core.db_handler import get_notion_data, update_srs_data, get_due_questions, update_my_memo, refresh_notion_images

# アプリのバージョン（キャッシュ更新を促すため）
APP_VERSION = "2026.03.18.v2"

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
        border-left: 10px solid #dc3545;
    }
    .exp-box {
        background-color: #f1f3f5;
        padding: 10px;
        border-radius: 5px;
        font-size: 0.95em;
        margin-top: 5px;
        line-height: 1.6;
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
    div[data-testid="stRadio"] input {
        display: none;
    }
    
    .version-info {
        font-size: 0.7em;
        color: #ccc;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

def render_exp_with_latex(text):
    """
    解説文中の $ ... $ を検知し、数式として確実にレンダリングする。
    インラインで崩れる可能性を考慮し、数式部分は $$ ... $$ に変換して強調表示を試みる。
    """
    if not text:
        return "解説なし"
    
    # 単純な $...$ を $$...$$ に変換してブロック表示を強制する（視認性向上）
    # すでに $$ が使われている場合はそのまま
    processed_text = re.sub(r'(?<!\$)\$(?!\$)(.*?)\$', r'\n$$\1$$\n', text)
    
    st.markdown(processed_text)

def main():
    # 画面最上部にバージョン情報を表示
    st.markdown(f'<p class="version-info">ver {APP_VERSION}</p>', unsafe_allow_html=True)
    
    st.title("🧠 建築設備士 択一クイズ")

    if 'all_notion_data' not in st.session_state:
        with st.spinner("Notionからデータを読み込み中..."):
            st.session_state.all_notion_data = get_notion_data()

    if not st.session_state.all_notion_data:
        st.error("Notionからデータが取得できませんでした。設定を確認してください。")
        return

    available_sections = sorted(list(set([q['section'] for q in st.session_state.all_notion_data if q.get('section')])))
    
    st.subheader("📂 学習する分野を選択")
    section_options = ["全分野"] + available_sections
    selected_section_label = st.selectbox("分野をタップして選択してください：", options=section_options, index=0)
    
    st.sidebar.header("⚙️ 学習モード")
    mode = st.sidebar.radio("モード", ["忘却曲線モード", "全問トレーニング"])

    selected_sections = [] if selected_section_label == "全分野" else [selected_section_label]

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
        
        if not qs:
            st.session_state.questions = []
        else:
            random.shuffle(qs)
            st.session_state.questions = qs
            st.session_state.idx = 0
            st.session_state.ans = False
            st.session_state.selected = None

    if not st.session_state.questions:
        st.info("💡 選択された分野には現在回答すべき問題がありません。『全分野』にするか『全問トレーニング』モードをお試しください。")
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

# ヘッダー情報のレイアウト
head_col1, head_col2 = st.columns([2, 1])

with head_col1:
    st.info(f"【{mode}】 {st.session_state.idx + 1} / {len(st.session_state.questions)} (ID: {q['q_id']})")
    if q.get("exam_info"):
        st.caption(f"📅 {q['exam_info']}")

with head_col2:
    diff = q.get("difficulty", "")
    if diff == "A":
        st.markdown('<div style="background-color: #d4edda; color: #155724; padding: 10px; border-radius: 10px; text-align: center; border: 1px solid #c3e6cb; font-weight: bold;">ランクA [初級]</div>', unsafe_allow_html=True)
    elif diff == "B":
        st.markdown('<div style="background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 10px; text-align: center; border: 1px solid #ffeeba; font-weight: bold;">ランクB [中級]</div>', unsafe_allow_html=True)
    elif diff == "C":
        st.markdown('<div style="background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 10px; text-align: center; border: 1px solid #f5c6cb; font-weight: bold;">ランクC [上級]</div>', unsafe_allow_html=True)

st.subheader(q["question"])


    if not st.session_state.ans:
        choices = [c for c in q["choices"] if c]
        user_choice = st.radio("選択してください：", choices, index=None, key=f"q_{st.session_state.idx}")
        
        if st.button("回答を確定", type="primary", use_container_width=True):
            if user_choice:
                st.session_state.selected = user_choice
                st.session_state.ans = True
                with st.spinner("最新の画像を読み込み中..."):
                    st.session_state.current_image_urls = refresh_notion_images(q['page_id'])
                st.rerun()
            else:
                st.warning("選択肢を選んでください。")
    else:
        ans_raw = str(q["answer"]).strip()
        correct_idx = int(ans_raw) - 1 if ans_raw.isdigit() else -1
        correct_text = q["choices"][correct_idx] if correct_idx >= 0 else None
        is_correct = (st.session_state.selected == correct_text)

        # 1. 各肢の詳細解説
        st.divider()
        st.markdown("### 📝 各肢の詳細解説")
        for i in range(4):
            choice_text = q["choices"][i]
            if not choice_text: continue
            exp_text = q["exps"][i] if i < len(q["exps"]) else ""
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
                    <strong>解説:</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 数式レンダリングを考慮した解説表示
            render_exp_with_latex(exp_text)

        # 2. 正誤判定
        st.divider()
        if is_correct:
            st.success(f"⭕ 正解！ (正解：肢 {ans_raw})")
        else:
            st.error(f"❌ 不正解... (正解：肢 {ans_raw})")
        
        st.info("💡 さらに詳しく知りたい場合は、サイドバーの「4_AI_Tutor」へ相談してください。")

        # 3. 画像
        current_images = st.session_state.get("current_image_urls", [])
        if current_images:
            for url in current_images:
                st.divider()
                st.image(url, use_container_width=True, caption=f"【図解】{q['q_id']}")

        # 4. メモ
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

        # SRSボタン
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
                if memo_key in st.session_state:
                    del st.session_state[memo_key]
                if "current_image_urls" in st.session_state:
                    del st.session_state["current_image_urls"]
                st.rerun()

if __name__ == "__main__":
    main()
