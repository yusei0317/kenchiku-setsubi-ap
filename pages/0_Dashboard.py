import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from core.db_handler import get_stats, get_master_data, get_notion_data

st.set_page_config(page_title="学習ポータル", layout="wide", initial_sidebar_state="auto")

# Professional Notion-like Theme
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    .main .block-container { padding-top: 2rem; max-width: 1000px; }
    .notion-card {
        background-color: #FFFFFF;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #E9ECEF;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        margin-bottom: 24px;
    }
    .header-card { border-left: 6px solid #1E3A8A; }
    .status-badge {
        display: inline-flex; align-items: center;
        background-color: #DCFCE7; color: #166534;
        padding: 4px 12px; border-radius: 9999px;
        font-size: 0.85rem; font-weight: 600; margin-bottom: 12px;
    }
    .action-card {
        background-color: #FFFFFF; padding: 20px; border-radius: 12px;
        border: 1px solid #E9ECEF; transition: all 0.2s ease-in-out;
        cursor: pointer; height: 100%;
    }
    .action-card:hover {
        transform: translateY(-4px); box-shadow: 0 12px 20px rgba(0, 0, 0, 0.06);
        border-color: #3B82F6;
    }
    .action-title { color: #1E3A8A; font-weight: 700; font-size: 1.1rem; margin-bottom: 8px; }
    .action-desc { color: #64748B; font-size: 0.85rem; line-height: 1.5; }
    .footer-text { text-align: center; color: #94A3B8; font-size: 0.8rem; margin-top: 40px; }
</style>
""", unsafe_allow_html=True)

def main():
    with st.spinner("最新の学習記録を取得中..."):
        all_data = get_notion_data()
        df_status, df_history = get_stats()
        
        # db_handler.py の get_master_data(df) は引数を取るため、生データからDFを作成
        df_raw = pd.DataFrame(all_data)
        master_ratio = get_master_data(df_raw)
        
        total_count = len(all_data)

    # 1. Header
    st.markdown(f"""
    <div class="notion-card header-card">
        <div class="status-badge">✅ Notionデータベース（{total_count}問）と同期中</div>
        <h1 style='margin: 0; color: #1E3A8A; font-size: 1.8rem;'>🏗️ 建築設備士 択一クイズ</h1>
        <p style='color: #475569; margin-top: 8px;'>合格への最短ルート。学習ポータルへようこそ。</p>
    </div>
    """, unsafe_allow_html=True)

    # 2. Study Footprint (GitHub style Heatmap)
    st.markdown('<div class="notion-card">', unsafe_allow_html=True)
    st.subheader("📅 学習の足跡")
    
    if not df_history.empty:
        df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
        daily_counts = df_history.groupby('timestamp').size().reset_index(name='counts')
        
        today = datetime.now().date()
        date_range = [today - timedelta(days=i) for i in range(90)]
        date_df = pd.DataFrame({'timestamp': pd.to_datetime(date_range)})
        
        heatmap_data = pd.merge(date_df, daily_counts, on='timestamp', how='left').fillna(0)
        heatmap_data['date_str'] = heatmap_data['timestamp'].dt.strftime('%Y-%m-%d')
        
        heatmap_data['weekday'] = heatmap_data['timestamp'].dt.weekday
        
        fig = px.density_heatmap(
            heatmap_data, x="timestamp", y="weekday", z="counts",
            color_continuous_scale="Viridis",
            labels={'counts': '回答数', 'weekday': '曜日'},
            range_z=[0, 10],
            height=200
        )
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        selected_date = st.select_slider(
            "詳細を表示する日付を選択:",
            options=heatmap_data['date_str'].tolist()[::-1],
            value=heatmap_data['date_str'].tolist()[0]
        )
        
        day_details = df_history[df_history['timestamp'].dt.strftime('%Y-%m-%d') == selected_date]
        if not day_details.empty:
            st.markdown(f"**{selected_date} の学習詳細:**")
            for _, row in day_details.iterrows():
                res = "⭕" if row['is_correct'] else "❌"
                st.caption(f"{res} 【{row['section']}】 ID: {row['question_id']}")
        else:
            st.caption(f"{selected_date} の記録はありません。")
    else:
        st.info("学習記録がまだありません。クイズを解いて草を生やしましょう！")
    st.markdown('</div>', unsafe_allow_html=True)

    # 3. Action Cards
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="action-card">
            <div class="action-title">📊 分析レポート</div>
            <div class="action-desc">セクション別の正答率や苦手な問題を特定します。</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("詳細を表示", key="btn_hist", use_container_width=True):
            st.toast("6_Historyページから確認できます。")

    with col2:
        st.markdown("""
        <div class="action-card">
            <div class="action-title">🧠 学習を再開</div>
            <div class="action-desc">忘却曲線に基づいた最適な復習メニューを生成します。</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("クイズを開始", key="btn_quiz", type="primary", use_container_width=True):
            st.toast("2_Quizページから開始してください。")

    # 4. Quick Stats
    st.subheader("📈 クイック統計")
    m_col1, m_col2, m_col3 = st.columns(3)
    
    total_q = total_count if total_count > 0 else 1
    started_q = len(df_status[df_status['reps'] > 0]) if not df_status.empty else 0

    with m_col1: st.metric("全体カバー率", f"{int(started_q/total_q*100)}%")
    with m_col2: st.metric("マスター率", f"{int(master_ratio*100)}%")
    with m_col3:
        acc = int(df_history['is_correct'].mean() * 100) if not df_history.empty else 0
        st.metric("総合正答率", f"{acc}%")

    st.markdown('<div class="footer-text">Powered by SM-2 Algorithm & Notion API</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
