import streamlit as st
import pandas as pd
import plotly.express as px
from core.db_handler import get_stats, get_master_data

st.set_page_config(page_title="学習履歴", layout="wide")

# Custom CSS for modern UI
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007bff !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("📊 学習履歴・分析")
    st.caption("Notionの最新データを基に学習進捗を分析します。")
    
    with st.spinner("データを取得中..."):
        df_status, df_history = get_stats()
        df_all = get_master_data()
    
    if df_status.empty:
        st.warning("データがありません。クイズを解いて学習を始めてください。")
        return

    tab_analysis, tab_history = st.tabs(["進捗分析", "詳細ステータス"])
    
    with tab_analysis:
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("分野別正答率")
            # q_id から分野を抽出 (例: 7_1 -> 7_配管とポンプ)
            section_map = {"7": "7_配管とポンプ", "8": "8_ダクトと送風機", "10": "10_排煙設備"}
            
            # historyが空でない場合のみグラフ表示
            valid_history = df_history[df_history['timestamp'].notna()].copy()
            if not valid_history.empty:
                valid_history['section_code'] = valid_history['question_id'].apply(lambda x: x.split('_')[0])
                valid_history['section'] = valid_history['section_code'].map(section_map).fillna("その他")
                
                section_acc = valid_history.groupby('section')['is_correct'].mean().reset_index()
                section_acc['is_correct'] *= 100
                
                fig_section = px.bar(section_acc, x='section', y='is_correct', 
                                    labels={'is_correct': '正答率 (%)', 'section': '分野'},
                                    color='is_correct', color_continuous_scale='RdYlGn',
                                    range_y=[0, 100])
                st.plotly_chart(fig_section, use_container_width=True)
            else:
                st.info("正答率を表示するための履歴データがまだありません。")

        with col_right:
            st.subheader("習得レベル分布")
            level_counts = df_status['mastery_level'].value_counts().reset_index()
            level_counts.columns = ['レベル', '問題数']
            
            fig_level = px.pie(level_counts, values='問題数', names='レベル',
                              color='レベル',
                              color_discrete_map={'Mastered':'#28a745', 'Learning':'#ffc107', 'New':'#6c757d'})
            st.plotly_chart(fig_level, use_container_width=True)

    with tab_history:
        st.subheader("問題別ステータス一覧")
        # 表示用にカラム名を整える
        df_display = df_status.copy()
        df_display = df_display.rename(columns={
            'q_id': '問題ID',
            'reps': '正解回数',
            'interval': '復習間隔(日)',
            'last_answered': '最終回答日',
            'is_correct': '直近正解',
            'mastery_level': '習得状況'
        })
        
        # 最終回答日でソート
        df_display = df_display.sort_values('最終回答日', ascending=False)
        
        def color_status(val):
            if val == 'Mastered': return 'background-color: #e8f5e9'
            if val == 'Learning': return 'background-color: #fff9c4'
            return ''

        st.dataframe(df_display.style.applymap(color_status, subset=['習得状況']), use_container_width=True)

if __name__ == "__main__":
    main()
