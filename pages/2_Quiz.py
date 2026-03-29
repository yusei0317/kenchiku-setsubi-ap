import streamlit as st
import random
import re
from datetime import datetime
from core.db_handler import (
    get_notion_data, 
    update_srs_data, 
    get_due_questions, 
    update_my_memo, 
    refresh_notion_images, 
    clear_notion_cache
)

# アプリのバージョン
APP_VERSION = "2026.03.18.v6"

st.set_page_config(page_title="建築設備士 択一クイズ", layout="wide")

# デザイン：ライトテーマ & カード型
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    .quiz-card {
        background-color: #FFFFFF;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #E9ECEF;
    }
    .choice-card {
        background-color: #FFFFFF;
        padding: 15px 20px;
        border-radius: 10px;
        border: 1px solid #DEE2E6;
        margin-bottom: 10px;
        transition: all 0.2s;
    }
    .correct-card { border-left: 6px solid #28A745; background-color: #F4FFF6; }
    .incorrect-card { border-left: 6px solid #DC3545; background-color: #FFF5F5; }
    .exp-inner {
        font-size: 0.95em; line-height: 1.6; color: #495057;
        margin-top: 10px; padding: 10px; background-color: #F1F3F5; border-radius: 6px;
    }
    div[data-testid="stRadio"] > div { gap: 8px; }
    div[data-testid="stRadio"] label {
        background-color: white; padding: 18px 25px !important;
        border-radius: 12px; border: 1px solid #CED4DA; width: 100%;
        margin-bottom: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    div[data-testid="stRadio"] input { display: none; }
    .header-info { font-size: 0.9em; color: #6C757D; font-weight: 500; }
    .stats-badge {
        font-size: 0.85em; color: #495057; background: #E9ECEF;
        padding: 4px 12px; border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

def format_latex_text(text):
    """
    テキスト内のバックスラッシュをエスケープし、$ 記法を LaTeX として正しくレンダリング可能な形式に変換する。
    """
    if not text: return ""
    # バックスラッシュをエスケープ（Streamlit/Markdownの仕様対策）
    processed = text.replace('\\', '\\\\')
    # $...$ を検知し、ブロック表示 $$...$$ に変換して視認性を高める（オプション）
    processed = re.sub(r'(?<!\$)\$(?!\$)(.*?)\$', r'\n$$\1$$\n', processed)
    return processed

def main():
    st.sidebar.caption(f"ver {APP_VERSION}")
    st.title("🧠 建築設備士 択一クイズ")

    # データロード
    if 'all_notion_data' not in st.session_state:
        with st.spinner("Notionからデータを読み込み中..."):
            st.session_state.all_notion_data = get_notion_data()

    if not st.session_state.all_notion_data:
        st.error("データの読み込みに失敗しました。")
        return

    # 忘却曲線モードの実装
    st.sidebar.header("⚙️ 学習モード")
    srs_mode = st.sidebar.toggle("🧠 忘却曲線モード（復習優先）", value=True)
    mode_label = "全問トレーニング" if not srs_mode else "忘却曲線モード"

    # セクション取得
    available_sections = sorted(list(set([q['section'] for q in st.session_state.all_notion_data if q.get('section')])))
    
    st.markdown('<div class="quiz-card">', unsafe_allow_html=True)
    section_options = ["全分野"] + available_sections
    selected_section_label = st.selectbox("学習する分野を選択：", options=section_options, index=0)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.sidebar.button("🔄 データを強制更新"):
        clear_notion_cache()
        if 'all_notion_data' in st.session_state: del st.session_state.all_notion_data
        st.rerun()

    selected_sections = [] if selected_section_label == "全分野" else [selected_section_label]
    cfg_key = f"{mode_label}-{selected_sections}"
    
    if "last_cfg" not in st.session_state or st.session_state.last_cfg != cfg_key:
        if "questions" in st.session_state: del st.session_state.questions
        st.session_state.last_cfg = cfg_key

    if 'questions' not in st.session_state:
        due_ids = get_due_questions() if srs_mode else []
        
        qs = [
            q for q in st.session_state.all_notion_data 
            if (not selected_sections or q['section'] in selected_sections) and 
               (not srs_mode or q['q_id'] in due_ids)
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
        if srs_mode:
            st.success("🎉 現在、復習が必要な問題はありません！全問トレーニングモードに切り替えて学習を進めましょう。")
        else:
            st.info("💡 該当する問題がありません。")
        return

    # 進捗表示
    remaining = len(st.session_state.questions) - st.session_state.idx
    if srs_mode:
        st.write(f"📝 今日の復習対象：残り **{remaining}** 問")
    else:
        st.write(f"📝 進行中：**{st.session_state.idx + 1}** / {len(st.session_state.questions)}")

    if st.session_state.idx >= len(st.session_state.questions):
        st.balloons()
        st.success("🎉 全てのクイズが完了しました！")
        if st.button("もう一度最初から解く"):
            st.session_state.idx = 0
            random.shuffle(st.session_state.questions)
            st.rerun()
        return

    q = st.session_state.questions[st.session_state.idx]
    st.session_state.current_question = q

    # ヘッダー情報の整理
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <div class="header-info">📅 {q.get('exam_info', '年度不明')} | 🏷️ ランク{q.get('difficulty', '-')}</div>
        <div class="stats-badge">📈 解答:{q['reps']}回 | 🎯 正答率:{int(q['correct_count']/q['reps']*100) if q['reps']>0 else 0}%</div>
    </div>
    """, unsafe_allow_html=True)

    # 問題文の表示（LaTeX対応）
    st.markdown(f'<div class="quiz-card"><h3 style="margin:0;">{format_latex_text(q["question"])}</h3></div>', unsafe_allow_html=True)

    if not st.session_state.ans:
        # 解答フェーズ
        choices = [c for c in q["choices"] if c]
        user_choice = st.radio("選択肢をタップ：", choices, index=None, key=f"q_{st.session_state.idx}")
        
        if st.button("回答を確定", type="primary", use_container_width=True):
            if user_choice:
                st.session_state.selected = user_choice
                st.session_state.ans = True
                
                # 正誤判定
                ans_raw = str(q["answer"]).strip()
                correct_idx = int(ans_raw) - 1 if ans_raw.isdigit() else -1
                correct_text = q["choices"][correct_idx] if correct_idx >= 0 else None
                is_correct = (user_choice == correct_text)
                
                # 更新
                update_srs_data(q['page_id'], 2, q['interval'], q['ease_factor'], q['reps'], q['correct_count'], is_correct, q.get('history', ""))
                
                with st.spinner("画像を読み込み中..."):
                    st.session_state.current_image_urls = refresh_notion_images(q['page_id'])
                st.rerun()
            else:
                st.warning("選択肢を選んでください。")
    else:
        # 結果フェーズ
        ans_raw = str(q["answer"]).strip()
        correct_idx = int(ans_raw) - 1 if ans_raw.isdigit() else -1
        correct_text = q["choices"][correct_idx] if correct_idx >= 0 else None
        is_correct = (st.session_state.selected == correct_text)

        # 各肢の詳細解説
        st.markdown("### 📝 各肢の詳細解説")
        for i in range(4):
            choice_text = q["choices"][i]
            if not choice_text: continue
            exp_text = q["exps"][i] if i < len(q["exps"]) else ""
            is_this_correct = (i == correct_idx)
            is_this_selected = (st.session_state.selected == choice_text)
            
            card_class = "choice-card"
            if is_this_correct: card_class += " correct-card"
            elif is_this_selected: card_class += " incorrect-card"
            
            label = f"肢 {i+1}"
            if is_this_correct: label = f"🎯 {label} (正解)"
            elif is_this_selected: label = f"❌ {label} (あなたの選択)"
            
            st.markdown(f"""
            <div class="{card_class}">
                <strong>{label}</strong><br>{choice_text}
                <div class="exp-inner">
                    <strong>解説:</strong><br>{format_latex_text(exp_text)}
                </div>
            </div>
            """, unsafe_allow_html=True)

        if is_correct:
            st.success(f"⭕ 正解！ (正解：肢 {ans_raw})")
        else:
            st.error(f"❌ 不正解... (正解：肢 {ans_raw})")
        
        current_images = st.session_state.get("current_image_urls", [])
        if current_images:
            for url in current_images:
                st.image(url, use_container_width=True)

        with st.expander("🧠 思考の振り返りメモ", expanded=False):
            memo_key = f"memo_{q['page_id']}"
            if memo_key not in st.session_state: st.session_state[memo_key] = q.get("my_memo", "")
            memo_text = st.text_area("メモを入力：", value=st.session_state[memo_key], key=f"ta_{q['page_id']}")
            if st.button("メモを保存", key=f"save_{q['page_id']}", use_container_width=True):
                update_my_memo(q['page_id'], memo_text)
                st.toast("保存完了")

        st.divider()
        st.markdown("##### 復習タイミングを選択（SRS評価）")
        cols = st.columns(4)
        labels = [("もう一度", 0), ("難しい", 1), ("普通", 2), ("簡単", 3)]
        for i, (label, val) in enumerate(labels):
            if cols[i].button(label, key=f"srs_{val}", use_container_width=True):
                update_srs_data(q['page_id'], val, q['interval'], q['ease_factor'], q['reps'], q['correct_count'], is_correct, q.get('history', ""))
                st.session_state.idx += 1
                st.session_state.ans = False
                st.session_state.selected = None
                if memo_key in st.session_state: del st.session_state[memo_key]
                st.rerun()

if __name__ == "__main__":
    main()
