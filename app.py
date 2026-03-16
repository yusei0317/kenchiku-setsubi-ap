import streamlit as st
from core.db_handler import init_db, get_master_data

# initial_sidebar_state="auto" to allow users to toggle, but visible
st.set_page_config(page_title="建築設備士学習アプリ", layout="wide", initial_sidebar_state="auto")

# Stable CSS to fix mobile sidebar
st.markdown("""
<style>
    [data-testid="stHeader"] {
        z-index: 1000000 !important;
        background: rgba(255, 255, 255, 0.8) !important;
    }
    .stApp {
        background-color: #f8f9fa;
    }
    .welcome-card {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
init_db()

def main():
    st.title("🏗️ 建築設備士学習アプリ")
    
    # Help message for mobile
    st.info("👈 **左上のメニュー (≡ アイコン) から機能を選択してください**")

    with st.container():
        st.markdown("""
        <div class="welcome-card">
            <h3>📖 はじめに</h3>
            <p>このアプリは、建築設備士試験の対策を効率化するためのツールです。</p>
            <ul>
                <li><strong>ダッシュボード</strong>: 学習進捗と苦手分野を可視化。</li>
                <li><strong>クイズモード</strong>: 選択肢形式で実戦的な演習。</li>
                <li><strong>フラッシュカード</strong>: 隙間時間のクイック学習。</li>
            </ul>
            <p style='color: #666; font-size: 0.9em;'>※スマホでメニューが見えない場合は、左上の <b>「三」</b> アイコンをタップしてください。</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Load and check data
    df = get_master_data()
    if df.empty:
        st.warning("⚠️ `exam_db/1-7_haikantoponpu.csv` が見つからないか、空です。データを配置してください。")
    else:
        st.success(f"✅ 現在 {len(df)} 問のデータが読み込まれています。学習を始めましょう！")

if __name__ == "__main__":
    main()
