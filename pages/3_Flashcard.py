import streamlit as st
import json
import random
from core.db_handler import update_srs, get_due_questions

st.set_page_config(page_title="フラッシュカード", layout="wide", initial_sidebar_state="auto")

# Stable CSS for fixes
st.markdown("""
<style>
    /* 1. Mobile Sidebar Fix */
    [data-testid="stHeader"] {
        z-index: 1000000 !important;
        background: rgba(255, 255, 255, 0.8) !important;
    }
    
    /* 2. Layout Stability */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: auto;
        min-height: 3.2em;
        font-weight: bold;
    }
    .question-card {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        text-align: center;
        min-height: 140px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 15px;
    }
    .answer-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        border-top: 5px solid #28a745;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

def load_questions():
    with open('exam_db/questions.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    st.title("🎴 フラッシュカード学習")
    
    if 'flash_questions' not in st.session_state:
        all_questions = load_questions()
        due_ids = get_due_questions()
        
        if not due_ids:
            st.session_state.flash_questions = all_questions
            random.shuffle(st.session_state.flash_questions)
        else:
            st.session_state.flash_questions = [q for q in all_questions if q['question_id'] in due_ids]
            random.shuffle(st.session_state.flash_questions)
            
        st.session_state.flash_index = 0
        st.session_state.flash_show_answer = False

    if not st.session_state.flash_questions:
        st.success("🎉 現在復習すべきカードはありません！")
        return

    if st.session_state.flash_index >= len(st.session_state.flash_questions):
        st.balloons()
        st.success("カードの学習が完了しました！")
        if st.button("もう一度最初から"):
            st.session_state.flash_index = 0
            random.shuffle(st.session_state.flash_questions)
            st.rerun()
        return

    q = st.session_state.flash_questions[st.session_state.flash_index]
    
    # Progress
    st.caption(f"カード {st.session_state.flash_index + 1} / {len(st.session_state.flash_questions)}")
    
    # Question Card (Always visible)
    st.markdown(f"""
    <div class="question-card">
        <div>
            <div style="color: #666; font-size: 0.8em; margin-bottom: 5px;">{q['section_label']}</div>
            <div style="font-size: 1.2em; font-weight: 500;">{q['stem']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display choices even in flashcard mode if they exist
    if 'choices' in q:
        for choice in q['choices']:
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 10px 15px; margin: 5px 0; border-radius: 8px; border: 1px solid #ddd; text-align: left;">
                <strong>{choice['label']}:</strong> {choice['text']}
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    if not st.session_state.flash_show_answer:
        if st.button("解答を表示", type="primary", key=f"show_f_{st.session_state.flash_index}"):
            st.session_state.flash_show_answer = True
            st.rerun()
    else:
        # Answer Card (Appears below)
        st.markdown(f"""
        <div class="answer-card">
            <h2 style="color: #28a745; text-align: center; margin: 0;">正解: {q['answer']}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 解説")
        if isinstance(q['choice_explanations'], list):
            for exp in q['choice_explanations']:
                label = exp.get('label', '')
                text = exp.get('explanation', '')
                is_correct = (label == q['answer'])
                st.markdown(f"""
                <div style="background-color: {'#e8f5e9' if is_correct else '#fafafa'}; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 3px solid {'#2e7d32' if is_correct else '#ddd'}; text-align: left;">
                    <strong>{'✅' if is_correct else '💡'} 選択肢 {label}:</strong> {text}
                </div>
                """, unsafe_allow_html=True)

        st.divider()
        st.markdown("##### 記憶定着度を評価して次へ")
        
        # Anki-style Rating Buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("もう一度\n(1日後)", key=f"f_rate0_{st.session_state.flash_index}"):
                update_srs(q['question_id'], 0)
                next_card()
        with col2:
            if st.button("難しい\n(1日後)", key=f"f_rate1_{st.session_state.flash_index}"):
                update_srs(q['question_id'], 1)
                next_card()
        with col3:
            if st.button("普通\n(3日後)", key=f"f_rate2_{st.session_state.flash_index}"):
                update_srs(q['question_id'], 2)
                next_card()
        with col4:
            if st.button("簡単\n(15日後)", key=f"f_rate3_{st.session_state.flash_index}"):
                update_srs(q['question_id'], 3)
                next_card()

def next_card():
    st.session_state.flash_index += 1
    st.session_state.flash_show_answer = False
    st.rerun()

if __name__ == "__main__":
    main()
