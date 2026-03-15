import streamlit as st
import pandas as pd
from datetime import datetime
from core.db_handler import get_stats, get_master_data

st.set_page_config(page_title="ダッシュボード", layout="wide")

# Custom CSS for modern UI
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .todo-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #007bff;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .exam-countdown {
        text-align: center;
        padding: 20px;
        margin-bottom: 30px;
    }
    .big-action-button > button {
        width: 100%;
        height: 4em;
        font-size: 1.2em !important;
        border-radius: 15px !important;
        background-color: #007bff !important;
        color: white !important;
        font-weight: bold !important;
        margin-top: 10px;
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
        <h1 style='font-size: 2.5em; margin-bottom: 0;'>建築設備士試験まであと <span style='color: #ff4b4b;'>{max(0, days_left)}</span> 日</h1>
        <p style='color: #666;'>試験日: 2026-06-21</p>
    </div>
    """, unsafe_allow_html=True)

    # Data Loading
    df_status, df_history = get_stats()
    df_all = get_master_data()
    
    # Dashboard Content
    st.markdown("### 📋 今日の ToDo")
    
    with st.container():
        st.markdown('<div class="todo-card">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate some metrics
        daily_goal = 10
        today_str = today.strftime('%Y-%m-%d')
        today_history = df_history[df_history['timestamp'].str.contains(today_str)] if not df_history.empty else pd.DataFrame()
        today_done = len(today_history)
        
        with col1:
            st.metric("達成率", f"{min(100, int(today_done/daily_goal*100))}%")
        with col2:
            st.metric("残り", f"{max(0, daily_goal - today_done)}問")
        with col3:
            if not today_history.empty:
                acc = int(today_history['is_correct'].mean() * 100)
            else:
                acc = 0
            st.metric("正答率", f"{acc}%")
        with col4:
            st.metric("モード", "標準学習")
            
        # Progress Bar
        progress = min(1.0, today_done / daily_goal)
        st.progress(progress)
        st.write(f"あと {max(0, daily_goal - today_done)} 問で今日の目標達成")
        
        # Big Action Button
        st.markdown('<div class="big-action-button">', unsafe_allow_html=True)
        if st.button("▶ 苦手分野集中で9問スタート", type="primary"):
            st.toast("この機能は準備中です！")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    st.markdown("### 学習サマリー")
    sum_col1, sum_col2, sum_col3 = st.columns(3)
    
    total_q = len(df_all) if not df_all.empty else 1
    started_q = len(df_status)
    mastered_q = len(df_status[df_status['mastery_level'] == 'Mastered'])
    
    with sum_col1:
        total_acc = int(df_history['is_correct'].mean() * 100) if not df_history.empty else 0
        st.metric("全体正答率", f"{total_acc}%")
    with sum_col2:
        st.metric("カバー率", f"{int(started_q/total_q*100)}%", help="一度でも解いた問題の割合")
    with sum_col3:
        st.metric("マスター率", f"{int(mastered_q/total_q*100)}%")

if __name__ == "__main__":
    main()
