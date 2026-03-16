import streamlit as st
import json
import os
import random
import requests
from core.db_handler import update_srs, get_due_questions

st.set_page_config(page_title="クイズモード", layout="wide", initial_sidebar_state="auto")

# Stable CSS for fixes
st.markdown("""
<style>
    /* 1. Mobile Sidebar Fix */
    [data-testid="stHeader"] {
        z-index: 1000000 !important;
        background: rgba(255, 255, 255, 0.8) !important;
    }
    
    /* 2. Button and Layout Stability */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: auto;
        min-height: 3.2em;
        font-weight: bold;
        text-align: left;
        padding: 10px 15px;
        white-space: normal;
        margin-bottom: 5px;
    }
    
    .question-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin-bottom: 15px;
        min-height: 120px;
    }
    
    .answer-box {
        background-color: #e7f3ff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# === Notionから画像を引っ張ってくる関数 ===
@st.cache_data(ttl=600)
def get_notion_images():
    try:
        token = st.secrets["notion"]["notion_token"]
        db_id = st.secrets["notion"]["database_id"]
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers)
        results = response.json().get("results", [])
        
        image_map = {}
        for item in results:
            props = item.get("properties", {})
            title_prop = props.get("id", {}).get("title", [])
            q_id = title_prop[0].get("plain_text", "") if title_prop else ""
            
            img_url = None
            img_prop = props.get("image", {}).get("files", [])
            if img_prop:
                if img_prop[0].get("type") == "file":
                    img_url = img_prop[0].get("file", {}).get("url")
                elif img_prop[0].get("type") == "external":
                    img_url = img_prop[0].get("external", {}).get("url")
                    
            if q_id and img_url:
                image_map[q_id] = img_url
        return image_map
    except Exception as e:
        return {}
# ============================================

def load_questions():
    with open('exam_db/questions.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    st.title("🧠 クイズモード (SRS学習)")
    
    if 'questions' not in st.session_state:
        all_questions = load_questions()
        due_ids = get_due_questions()
        
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
        if st.button("全問題から学習する", key="reset_all"):
            del st.session_state.questions
            st.rerun()
        return

    if st.session_state.current_index >= len(st.session_state.questions):
        st.balloons()
        st.success("本日の学習セッションが完了しました！")
        if st.button("もう一度最初から", key="restart"):
            st.session_state.current_index = 0
            random.shuffle(st.session_state.questions)
            st.session_state.show_answer = False
            st.session_state.user_choice = None
            st.rerun()
        return

    q = st.session_state.questions[st.session_state.current_index]
    
    st.caption(f"問題 {st.session_state.current_index + 1} / {len(st.session_state.questions)}")
    
    st.markdown(f"""
    <div class="question-box">
        <div style="color: #666; font-size: 0.8em;">{q['section_label']} - Q{q['question_no']}</div>
        <div style="font-size: 1.1em; margin-top: 5px;">{q['stem']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.show_answer:
        st.markdown("##### 選択肢を選択してください")
        for choice in q['choices']:
            btn_key = f"choice_{st.session_state.current_index}_{choice['label']}"
            if st.button(f"{choice['label']}: {choice['text']}", key=btn_key):
                st.session_state.user_choice = choice['label']
                st.session_state.show_answer = True
                st.rerun()
        
        if st.button("解答だけ表示する", key=f"show_raw_{st.session_state.current_index}"):
            st.session_state.user_choice = None
            st.session_state.show_answer = True
            st.rerun()
    else:
        for choice in q['choices']:
            is_correct = (choice['label'] == q['answer'])
            was_selected = (choice['label'] == st.session_state.user_choice)
            
            border_style = "2px solid #28a745" if is_correct else ("2px solid #dc3545" if was_selected else "1px solid #ddd")
            bg_color = "#d4edda" if is_correct else ("#f8d7da" if was_selected else "#f0f2f6")
            icon = "✅ " if is_correct else ("❌ " if was_selected else "")
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 10px 15px; margin: 5px 0; border-radius: 8px; border: {border_style}; text-align: left;">
                <strong>{icon}{choice['label']}:</strong> {choice['text']}
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        if st.session_state.user_choice:
            if st.session_state.user_choice == q['answer']:
                st.success(f"✨ 正解！ (回答: {st.session_state.user_choice})")
            else:
                st.error(f"❌ 不正解... (回答: {st.session_state.user_choice}, 正解: {q['answer']})")
        
        st.markdown("#### 解説")
        if isinstance(q['choice_explanations'], list):
            for exp in q['choice_explanations']:
                label = exp.get('label', '')
                text = exp.get('explanation', '')
                is_correct_label = (label == q['answer'])
                
                st.markdown(f"""
                <div style="background-color: {'#e8f5e9' if is_correct_label else '#fafafa'}; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 3px solid {'#2e7d32' if is_correct_label else '#ddd'};">
                    <strong>選択肢 {label}:</strong> {text}
                </div>
                """, unsafe_allow_html=True)
        
        # === Notionと合体して画像を表示する部分 ===
        notion_images = get_notion_images()
        if q['question_id'] in notion_images:
            with st.expander("🖼️ 図解を見る (Notionより)", expanded=True):
                st.image(notion_images[q['question_id']], use_container_width=True)
        # ========================================

        st.divider()
        st.markdown("##### 難易度を評価して次へ")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("もう一度\n(1日後)", key=f"rate0_{st.session_state.current_index}"):
                update_srs(q['question_id'], 0)
                next_question()
        with col2:
            if st.button("難しい\n(1日後)", key=f"rate1_{st.session_state.current_index}"):
                update_srs(q['question_id'], 1)
                next_question()
        with col3:
            if st.button("普通\n(3日後)", key=f"rate2_{st.session_state.current_index}"):
                update_srs(q['question_id'], 2)
                next_question()
        with col4:
            if st.button("簡単\n(15日後)", key=f"rate3_{st.session_state.current_index}"):
                update_srs(q['question_id'], 3)
                next_question()

def next_question():
    st.session_state.current_index += 1
    st.session_state.show_answer = False
    st.session_state.user_choice = None
    st.rerun()

if __name__ == "__main__":
    main()
