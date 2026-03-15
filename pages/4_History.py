import streamlit as st
import pandas as pd
import plotly.express as px
from core.db_handler import get_stats, get_master_data

st.set_page_config(page_title="学習履歴", layout="wide")

# Custom CSS for modern UI
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007bff !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("📊 学習履歴")
    
    df_status, df_history = get_stats()
    df_all = get_master_data()
    
    tab_analysis, tab_history, tab_session = st.tabs(["分析", "回答履歴", "セッション"])
    
    with tab_analysis:
        st.subheader("正答率トレンド (直近30回)")
        if not df_history.empty:
            # Prepare trend data
            df_history['date'] = pd.to_datetime(df_history['timestamp']).dt.date
            # Take last 30 entries
            trend_df = df_history.tail(30).copy()
            trend_df['rolling_acc'] = trend_df['is_correct'].rolling(window=5, min_periods=1).mean() * 100
            
            fig_trend = px.line(trend_df, x=trend_df.index, y='rolling_acc', 
                               labels={'index': '試行回数', 'rolling_acc': '正答率 (%)'},
                               title='直近の正答率推移 (5件移動平均)',
                               markers=True)
            fig_trend.update_layout(yaxis_range=[0, 105], template="plotly_white")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("データが不足しているためトレンドグラフを表示できません。")

        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("分野別正答率")
            if not df_history.empty and not df_all.empty:
                # Merge with master data to get section info
                df_merged = df_history.merge(df_all[['id', 'section']], left_on='question_id', right_on='id')
                section_acc = df_merged.groupby('section')['is_correct'].mean().reset_index()
                section_acc['is_correct'] *= 100
                
                fig_section = px.bar(section_acc, x='section', y='is_correct', 
                                    labels={'is_correct': '正答率 (%)', 'section': '分野'},
                                    color='is_correct', color_continuous_scale='RdYlGn')
                fig_section.update_layout(yaxis_range=[0, 105], template="plotly_white")
                st.plotly_chart(fig_section, use_container_width=True)
            else:
                st.info("データがありません。")

        with col_right:
            st.subheader("難易度別正答率")
            if not df_history.empty and not df_all.empty:
                # Merge with master data to get difficulty info
                df_merged = df_history.merge(df_all[['id', 'difficulty']], left_on='question_id', right_on='id')
                diff_acc = df_merged.groupby('difficulty')['is_correct'].mean().reset_index()
                diff_acc['is_correct'] *= 100
                
                fig_diff = px.bar(diff_acc, x='difficulty', y='is_correct', 
                                 labels={'is_correct': '正答率 (%)', 'difficulty': '難易度'},
                                 color='difficulty', color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_diff.update_layout(yaxis_range=[0, 105], template="plotly_white")
                st.plotly_chart(fig_diff, use_container_width=True)
            else:
                st.info("データがありません。")

    with tab_history:
        st.subheader("全回答履歴")
        if not df_history.empty:
            st.dataframe(df_history.sort_values('timestamp', ascending=False), use_container_width=True)
        else:
            st.info("回答履歴はまだありません。")

    with tab_session:
        st.subheader("セッション履歴")
        st.write("各学習セッション（開始から終了まで）の記録がここに表示されます。")
        st.info("現在開発中です。")

if __name__ == "__main__":
    main()
