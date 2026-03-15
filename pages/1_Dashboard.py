import streamlit as st
import pandas as pd
from datetime import datetime
from core.db_handler import get_stats, get_master_data

# initial_sidebar_state="auto" to allow users to toggle, but visible
st.set_page_config(page_title="ダッシュボード", layout="wide", initial_sidebar_state="auto")

# Stable CSS to prevent layout shift and fix mobile sidebar
st.markdown("""
<style>
    /* 1. Mobile Sidebar Fix: Ensure header and toggle are accessible */
    [data-testid="stHeader"] {
        z-index: 1000000 !important;
        background: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(10px);
    }
    
    /* 2. Prevent UI Shaking: Stable containers */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Fixed height metrics and cards to prevent jumping */
    div[data-testid="stMetric"] {
        background-color: white !important;
        padding: 15px !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        min-height: 100px;
    }

    .todo-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #007bff;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        min-height: 300px; /* Stabilize height */
    }

    .exam-countdown {
        text-align: center;
        padding: 10px;
        margin-bottom: 20px;
    }
    
    /* Responsive button */
    .big-action-button button {
        width: 100% !important;
        height: 3.5em !important;
        font-size: 1.1em !important;
        border-radius: 12px !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Countdown Section
    exam_date = datetime(2026, 6, 21)
    today = datetime.now()
    days_left = (exam_date - today).days
    
    st.markdown(f"""
    <div class="exam-countdown">
        <h2 style='margin-bottom: 0;'>建築設備士試験まであと <span style='color: #ff4b4b;'>{max(0, days_left)}</span> 日</h2>
        <p style='color: #666; font-size: 0.9em;'>試験日: 2026-06-21</p>
    </div>
    """, unsafe_allow_html=True)

    # Data Loading (Stable)
    df_status, df_history = get_stats()
    df_all = get_master_data()
    
    # Dashboard Content
    st.subheader("📋 今日の ToDo")
    
    # Use a simple container without complex div nesting for stability
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        
        daily_goal = 10
        today_str = today.strftime('%Y-%m-%d')
        today_history = df_history[df_history['timestamp'].str.contains(today_str)] if not df_history.empty else pd.DataFrame()
        today_done = len(today_history)
        
        with col1:
            st.metric("達成率", f"{min(100, int(today_done/daily_goal*100))}%")
        with col2:
            st.metric("残り", f"{max(0, daily_goal - today_done)}問")
        with col3:
            acc = int(today_history['is_correct'].mean() * 100) if not today_history.empty else 0
            st.metric("正答率", f"{acc}%")
        with col4:
            st.metric("モード", "標準学習")
            
        st.progress(min(1.0, today_done / daily_goal))
        st.caption(f"あと {max(0, daily_goal - today_done)} 問で今日の目標達成")
        
        # Action Button (No rerun inside main loop without event)
        if st.button("▶ 苦手分野集中で9問スタート", type="primary", use_container_width=True):
            st.toast("機能準備中です。クイズメニューをお使いください。")

    st.markdown("### 📊 学習サマリー")
    sum_col1, sum_col2, sum_col3 = st.columns(3)
    
    total_q = len(df_all) if not df_all.empty else 1
    started_q = len(df_status)
    mastered_q = len(df_status[df_status['mastery_level'] == 'Mastered'])
    
    with sum_col1:
        total_acc = int(df_history['is_correct'].mean() * 100) if not df_history.empty else 0
        st.metric("全体正答率", f"{total_acc}%")
    with sum_col2:
        st.metric("カバー率", f"{int(started_q/total_q*100)}%")
    with sum_col3:
        st.metric("マスター率", f"{int(mastered_q/total_q*100)}%")

if __name__ == "__main__":
    main()
