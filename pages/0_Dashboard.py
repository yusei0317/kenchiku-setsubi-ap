import streamlit as st
import pandas as pd
from datetime import datetime
from core.db_handler import get_stats, get_master_data, get_notion_data

st.set_page_config(page_title="学習ポータル", layout="wide", initial_sidebar_state="auto")

# 劇的なデザイン刷新: Notion-like & Professional
st.markdown("""
<style>
    /* 全体背景 */
    .stApp {
        background-color: #F8F9FA;
    }

    /* メインコンテナの余白調整 */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1000px;
    }

    /* 共通カードスタイル */
    .notion-card {
        background-color: #FFFFFF;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #E9ECEF;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        margin-bottom: 24px;
    }

    /* ヘッダーカード */
    .header-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F1F4F9 100%);
        border-left: 6px solid #1E3A8A;
    }

    /* ステータスバッジ */
    .status-badge {
        display: inline-flex;
        align-items: center;
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 12px;
    }

    /* アクションカード (Hover効果付き) */
    .action-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E9ECEF;
        transition: all 0.2s ease-in-out;
        cursor: pointer;
        height: 100%;
    }
    .action-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 20px rgba(0, 0, 0, 0.06);
        border-color: #3B82F6;
    }
    .action-title {
        color: #1E3A8A;
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .action-desc {
        color: #64748B;
        font-size: 0.85rem;
        line-height: 1.5;
    }

    /* ハイライトカード (今日の重点) */
    .highlight-card {
        background-color: #FFFBEB;
        border: 1px solid #FEF3C7;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin: 24px 0;
    }
    .highlight-text {
        color: #92400E;
        font-size: 1.05rem;
    }
    .emphasis {
        font-weight: 800;
        color: #B45309;
        font-size: 1.2rem;
        border-bottom: 2px solid #FDE68A;
    }

    /* フッター */
    .footer-text {
        text-align: center;
        color: #94A3B8;
        font-size: 0.8rem;
        margin-top: 40px;
        padding-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # データ取得
    with st.spinner("Notionと同期中..."):
        all_data = get_notion_data()
        df_status, df_history = get_stats()
        df_all = get_master_data()
        total_count = len(all_data)

    # 1. Header & Status
    st.markdown(f"""
    <div class="notion-card header-card">
        <div class="status-badge">✅ Notionデータベース（{total_count}問）と同期中</div>
        <h1 style='margin: 0; color: #1E3A8A; font-size: 1.8rem;'>🏗️ 建築設備士 択一クイズ</h1>
        <p style='color: #475569; margin-top: 8px;'>合格への最短ルート。学習ポータルへようこそ。</p>
    </div>
    """, unsafe_allow_html=True)

    # 2. Countdown & Metrics
    exam_date = datetime(2026, 6, 21)
    days_left = (exam_date - datetime.now()).days
    
    st.markdown(f"""
    <div style='text-align: right; margin-bottom: 10px; color: #64748B; font-weight: 600;'>
        試験本番まであと <span style='color: #EF4444; font-size: 1.2rem;'>{max(0, days_left)}</span> 日
    </div>
    """, unsafe_allow_html=True)

    # 3. Action Cards (2列)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="action-card">
            <div class="action-title">📊 学習状況の確認</div>
            <div class="action-desc">
                これまでの正答率や習得レベルを詳細に分析します。苦手分野を特定し、効率的な戦略を立てましょう。
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("分析レポートを開く", use_container_width=True):
            st.toast("左メニューの「6_History」から詳細を確認できます。")

    with col2:
        st.markdown("""
        <div class="action-card">
            <div class="action-title">🧠 トレーニング開始</div>
            <div class="action-desc">
                忘却曲線に基づいた復習、または特定分野の集中対策を開始します。毎日の積み重ねが合格をたぐり寄せます。
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("クイズをスタート", type="primary", use_container_width=True):
            st.toast("左メニューの「2_Quiz」から開始してください。")

    # 4. Highlight Card (今日の重点)
    st.markdown("""
    <div class="highlight-card">
        <div class="highlight-text">
            💡 <b>今日の重点ポイント</b><br>
            機械排煙設備の排煙機能力基準は <span class="emphasis">2 m³/s</span> 以上です。<br>
            この「数値」を確実に暗記しましょう。
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 5. Quick Stats
    st.subheader("📈 クイック統計")
    m_col1, m_col2, m_col3 = st.columns(3)
    
    total_q = len(df_all) if not df_all.empty else 1
    started_q = len(df_status[df_status['reps'] > 0]) if not df_status.empty else 0
    mastered_q = len(df_status[df_status['mastery_level'] == 'Mastered']) if not df_status.empty else 0

    with m_col1:
        st.metric("全体カバー率", f"{int(started_q/total_q*100)}%", help="一度でも解いた問題の割合")
    with m_col2:
        st.metric("マスター率", f"{int(mastered_q/total_q*100)}%", help="定着済みと判定された問題")
    with m_col3:
        total_acc = int(df_history['is_correct'].mean() * 100) if not df_history.empty else 0
        st.metric("総合正答率", f"{total_acc}%")

    # 6. Footer
    st.markdown("""
    <div class="footer-text">
        Powered by SM-2 Spaced Repetition Algorithm<br>
        記憶管理システムが有効です
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
