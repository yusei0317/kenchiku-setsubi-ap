import streamlit as st
import pandas as pd
from db_handler import DBHandler
import random

# Page config
st.set_page_config(page_title="資格試験学習アプリ", layout="wide")

# Initialize database
db = DBHandler()
db.load_questions_from_json()

# Session State Initialization
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'selected_section' not in st.session_state:
    st.session_state.selected_section = None
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'user_choice' not in st.session_state:
    st.session_state.user_choice = None

def reset_questions(section):
    st.session_state.questions = db.get_questions_by_section(section)
    random.shuffle(st.session_state.questions)
    st.session_state.current_question_index = 0
    st.session_state.answered = False
    st.session_state.user_choice = None

# Sidebar
st.sidebar.title("メニュー")
sections = db.get_sections()
selected_section = st.sidebar.selectbox("分野を選択してください", sections)

if selected_section != st.session_state.selected_section:
    st.session_state.selected_section = selected_section
    reset_questions(selected_section)

if st.sidebar.button("問題をリセット（シャッフル）"):
    reset_questions(selected_section)

# Main Page
st.title(f"学習アプリ: {selected_section}")

if not st.session_state.questions:
    st.warning("問題が見つかりませんでした。")
else:
    q = st.session_state.questions[st.session_state.current_question_index]
    
    # Progress Bar
    progress = (st.session_state.current_question_index) / len(st.session_state.questions)
    st.progress(progress)
    st.write(f"問題 {st.session_state.current_question_index + 1} / {len(st.session_state.questions)}")
    
    # Question Card
    with st.container():
        st.markdown(f"### Q{q['question_no']}: {q['section_label']} (難易度: {q['difficulty']})")
        st.write(q['stem'])
        
        # Choices
        if isinstance(q['choices'], list) and len(q['choices']) > 0 and isinstance(q['choices'][0], dict):
            choice_labels = [c.get('label', '') for c in q['choices']]
            choice_texts = [f"{c.get('label', '')}: {c.get('text', '')}" for c in q['choices']]
        else:
            choice_labels = []
            choice_texts = []
        
        # Use a form for radio selection to avoid immediate rerun if needed, 
        # but here we manage state manually for better feedback.
        user_selection = st.radio("選択肢:", choice_texts, index=None, key=f"radio_{st.session_state.current_question_index}")
        
        if st.button("回答する") and user_selection and not st.session_state.answered:
            st.session_state.answered = True
            st.session_state.user_choice = user_selection.split(":")[0]
            is_correct = st.session_state.user_choice == q['answer']
            db.save_result(q['question_id'], is_correct)
            st.rerun()

    # Feedback Area
    if st.session_state.answered:
        correct_answer = q['answer']
        is_correct = st.session_state.user_choice == correct_answer
        
        if is_correct:
            st.success("正解！")
        else:
            st.error(f"不正解... (正解: {correct_answer})")
        
        st.markdown("#### 解説")
        if isinstance(q['choice_explanations'], list):
            for exp in q['choice_explanations']:
                if isinstance(exp, dict):
                    label = exp.get('label', '')
                    explanation = exp.get('explanation', '')
                    prefix = "✅" if label == correct_answer else "❌"
                    st.write(f"{prefix} **選択肢 {label}**: {explanation}")
        elif isinstance(q['choice_explanations'], str):
            st.write(q['choice_explanations'])

        # Navigation
        if st.session_state.current_question_index < len(st.session_state.questions) - 1:
            if st.button("次の問題へ"):
                st.session_state.current_question_index += 1
                st.session_state.answered = False
                st.session_state.user_choice = None
                st.rerun()
        else:
            st.balloons()
            st.write("この分野の全問題を解き終わりました！")
            if st.button("最初から解き直す"):
                reset_questions(selected_section)
                st.rerun()

# Statistics in Sidebar or separate area
st.sidebar.markdown("---")
st.sidebar.subheader("学習状況")
stats = db.get_stats()
if stats:
    df_stats = pd.DataFrame(stats, columns=['分野', '解答数', '正解数'])
    df_stats['正解率'] = (df_stats['正解数'] / df_stats['解答数'] * 100).round(1).astype(str) + '%'
    st.sidebar.table(df_stats)
else:
    st.sidebar.info("まだ解答データがありません。")
