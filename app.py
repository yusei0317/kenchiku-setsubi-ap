import streamlit as st
from core.db_handler import get_notion_data

# 1. ページ設定（アプリのタイトルとレイアウトを定義）
st.set_page_config(page_title="建築設備士 SRS学習アプリ", layout="wide")

def main():
    # タイトルとウェルカムメッセージ
    st.title("🏗️ 建築設備士 合格戦略アプリ")
    st.write("ようこそ、後藤さん。2026年3月の試験合格に向けて、効率的に知識を定着させましょう。")

    # 2. Notionの接続確認（裏側で静かに実行）
    try:
        data = get_notion_data()
        if data:
            st.success(f"✅ Notionデータベース（{len(data)}問）と正常に同期しています。")
            
            # 視認性の高いナビゲーション
            col1, col2 = st.columns(2)
            with col1:
                st.info("📊 **学習状況の確認**\n\n左メニューの「1_Dashboard」から現在の習得率をチェックできます。")
            with col2:
                st.info("🧠 **トレーニング開始**\n\n「2_Quiz」で分野別の集中対策や、忘却曲線に基づいた復習が可能です。")
        else:
            st.warning("⚠️ Notionに接続されましたが、データが見つかりません。")
    except Exception as e:
        st.error("❌ Notionとの接続に失敗しました。Secretsの設定を再確認してください。")
        st.caption(f"詳細: {e}")

    st.divider()
    
    # 学習のヒント
    st.subheader("💡 今日の重点ポイント")
    st.write(r"機械排煙設備の排煙機能力基準は $2\,m^3/s$ 以上です。こうした重要な「数値」を、クイズの全問トレーニングで繰り返し叩き込みましょう。")
    st.caption("SM-2 アルゴリズムによる記憶管理が有効になっています。")

if __name__ == "__main__":
    main()
