import streamlit as st
import json
import os
import random
from core.db_handler import update_srs, get_due_questions

st.set_page_config(page_title="クイズモード", layout="wide")

# Custom CSS for Anki-like UI
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        height: auto;
        min-height: 3em;
        font-weight: bold;
        text-align: left;
        padding: 10px 20px;
        white-space: normal;
        display: block;
    }
    .question-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin-bottom: 20px;
    }
    .answer-box {
        background-color: #e7f3ff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin-top: 20px;
    }
    .choice-box {
        margin: 10px 0;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 5px;
    }
    .correct-choice {
        background-color: #d4edda;
        border-color: #c3e6cb;
    }
    /* Rating Buttons */
    .btn-again { background-color: #ff4b4b !important; color: white !important; }
    .btn-hard { background-color: #ffa500 !important; color: white !important; }
    .btn-good { background-color: #007bff !important; color: white !important; }
    .btn-easy { background-color: #28a745 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

def load_questions():
    with open('exam_db/questions.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    st.title("🧠 クイズモード (SRS学習)")
    
    if 'questions' not in st.session_state:
        all_questions = load_questions()
        due_ids = get_due_questions()
        
        # If no due questions, show all or some random ones
        if not due_ids:
            st.session_state.questions = all_questions
            random.shuffle(st.session_state.questions)
        else:
            st.session_state.questions = [q for q in all_questions if q['question_id'] in due_ids]
            random.shuffle(st.session_state.questions)
            
        st.session_state.current_index = 0
        st.session_state.show_answer = False
        st.session_state.user_choice = None

    if not st.session_state.questions:
        st.success("🎉 現在復習すべき問題はありません！")
        if st.button("全問題から学習する"):
            del st.session_state.questions
            st.rerun()
        return

    if st.session_state.current_index >= len(st.session_state.questions):
        st.balloons()
        st.success("本日の学習セッションが完了しました！")
        if st.button("もう一度最初から"):
            st.session_state.current_index = 0
            random.shuffle(st.session_state.questions)
            st.rerun()
        return

    q = st.session_state.questions[st.session_state.current_index]
    
    # Progress
    st.write(f"問題 {st.session_state.current_index + 1} / {len(st.session_state.questions)}")
    
    # Question Display (Always visible at top)
    st.markdown(f"""
    <div class="question-box">
        <h4>{q['section_label']} - Q{q['question_no']}</h4>
        <p style="font-size: 1.1em;">{q['stem']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Choices Display (Always visible)
    if not st.session_state.show_answer:
        st.write("### 選択肢を選択してください")
        for choice in q['choices']:
            if st.button(f"{choice['label']}: {choice['text']}", key=f"btn_{choice['label']}", use_container_width=True):
                st.session_state.user_choice = choice['label']
                st.session_state.show_answer = True
                st.rerun()
        
        if st.button("解答だけ表示する", key="show_raw"):
            st.session_state.user_choice = None
            st.session_state.show_answer = True
            st.rerun()
    else:
        # Show choices as static boxes when answer is revealed
        for choice in q['choices']:
            is_correct = (choice['label'] == q['answer'])
            was_selected = (choice['label'] == st.session_state.user_choice)
            
            border_style = "2px solid #28a745" if is_correct else ("2px solid #dc3545" if was_selected else "1px solid #ddd")
            bg_color = "#d4edda" if is_correct else ("#f8d7da" if was_selected else "#f0f2f6")
            icon = "✅ " if is_correct else ("❌ " if was_selected else "")
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 10px 20px; margin: 5px 0; border-radius: 5px; border: {border_style}; text-align: left;">
                <strong>{icon}{choice['label']}:</strong> {choice['text']}
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    if st.session_state.show_answer:
        # Answer Display
        if st.session_state.user_choice:
            is_correct = (st.session_state.user_choice == q['answer'])
            if is_correct:
                st.success(f"✨ 正解！ (あなたの回答: {st.session_state.user_choice})")
            else:
                st.error(f"❌ 不正解... (あなたの回答: {st.session_state.user_choice}, 正解: {q['answer']})")
        
        st.markdown(f"""
        <div class="answer-box">
            <h3>正解: {q['answer']}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 解説")
        if isinstance(q['choice_explanations'], list):
            for exp in q['choice_explanations']:
                label = exp.get('label', '')
                text = exp.get('explanation', '')
                is_correct_label = (label == q['answer'])
                was_user_choice = (label == st.session_state.user_choice)
                
                color = "#d4edda" if is_correct_label else ("#f8d7da" if was_user_choice else "#f0f2f6")
                st.markdown(f"""
                <div style="background-color: {color}; padding: 10px; margin: 5px 0; border-radius: 5px; text-align: left;">
                    <strong>選択肢 {label}:</strong> {text}
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        st.write("この問題の難易度はどうでしたか？")
        
        # Rating Buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("もう一度\n(1日後)", key="again"):
                update_srs(q['question_id'], 0)
                next_question()
        with col2:
            if st.button("難しい\n(1日後)", key="hard"):
                update_srs(q['question_id'], 1)
                next_question()
        with col3:
            if st.button("普通\n(3日後)", key="good"):
                update_srs(q['question_id'], 2)
                next_question()
        with col4:
            if st.button("簡単\n(15日後)", key="easy"):
                update_srs(q['question_id'], 3)
                next_question()

def next_question():
    st.session_state.current_index += 1
    st.session_state.show_answer = False
    st.session_state.user_choice = None
    st.rerun()

if __name__ == "__main__":
    main()
