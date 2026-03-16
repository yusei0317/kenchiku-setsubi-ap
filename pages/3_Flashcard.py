import streamlit as st
import random
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

# ページ設定
st.set_page_config(page_title="フラッシュカード", layout="wide", initial_sidebar_state="auto")

# CSSスタイル（ユーザーのこだわりデザインを継承）
st.markdown("""
<style>
    [data-testid="stHeader"] { z-index: 1000000 !important; background: rgba(255, 255, 255, 0.8) !important; }
    .stButton > button { width: 100%; border-radius: 8px; min-height: 3.2em; font-weight: bold; }
    .question-card {
        background-color: white; padding: 30px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #e0e0e0;
        text-align: center; min-height: 180px; display: flex;
        align-items: center; justify-content: center; margin-bottom: 15px;
    }
    .answer-card {
        background-color: #f8f9fa; padding: 20px; border-radius: 15px;
        border-top: 5px solid #28a745; margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🎴 フラッシュカード学習 (Notion連動)")

    # 1. セッション（データ取得）の初期化
    if 'flash_questions' not in st.session_state:
        with st.spinner("Notionから最新のカードを取得中..."):
            all_raw = get_notion_data()
            due_ids = get_due_questions()
            
            qs = []
            for item in all_raw:
                p = item.get("properties", {})
                qid = p.get("id", {}).get("title", [{}])[0].get("plain_text", "")
                
                # 今日の復習期限内、または未学習の問題のみ抽出
                if qid in due_ids:
                    qs.append({
                        "page_id": item.get("id"),
                        "q_id": qid,
                        "question": p.get("question", {}).get("rich_text", [{}])[0].get("plain_text", ""),
                        "answer": p.get("answer", {}).get("rich_text", [{}])[0].get("plain_text", ""),
                        "interval": p.get("interval", {}).get("number", 0) or 0,
                        "ease_factor": p.get("ease_factor", {}).get("number", 2.5) or 2.5,
                        "reps": p.get("reps", {}).get("number", 0) or 0
                    })
            
            random.shuffle(qs)
            st.session_state.flash_questions = qs
            st.session_state.flash_index = 0
            st.session_state.flash_show_answer = False

    # 全問終了時の処理
    if not st.session_state.flash_questions or st.session_state.flash_index >= len(st.session_state.flash_questions):
        st.balloons()
        st.success("🎉 今日の学習はすべて完了しました！")
        if st.button("もう一度最初から読み込む"):
            del st.session_state.flash_questions
            st.rerun()
        return

    # 現在の問題を取得
    q = st.session_state.flash_questions[st.session_state.flash_index]
    
    st.caption(f"カード {st.session_state.flash_index + 1} / {len(st.session_state.flash_questions)} (ID: {q['q_id']})")
    
    # 問題カード表示
    st.markdown(f"""
    <div class="question-card">
        <div>
            <div style="font-size: 1.3em; font-weight: 500; line-height: 1.6;">{q['question']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if not st.session_state.flash_show_answer:
        if st.button("解答を表示", type="primary"):
            st.session_state.flash_show_answer = True
            st.rerun()
    else:
        # 解答カード表示
        st.markdown(f"""
        <div class="answer-card">
            <h2 style="color: #28a745; text-align: center; margin: 0;">正解: {q['answer']}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # PDF自動マッピング
        pdf_prefix = q['q_id'].split('-')[0] if '-' in q['q_id'] else ""
        pdf_map = {"10": "10_排煙設備.pdf", "8": "8_ダクトと送風機.pdf", "7": "7_配管とポンプ.pdf"}
        pdf_name = pdf_map.get(pdf_prefix, "関連資料PDF")
        st.info(f"📚 参照資料: {pdf_name} を確認してください")

        st.divider()
        st.markdown("##### 記憶定着度を評価して次へ")
        
        # Anki方式の評価ボタン
        cols = st.columns(4)
        ratings = [("もう一度", 0), ("難しい", 1), ("普通", 2), ("簡単", 3)]
        
        for i, (label, val) in enumerate(ratings):
            if cols[i].button(label, key=f"rate_{val}"):
                with st.spinner("Notionに同期中..."):
                    # db_handlerの更新関数にすべてのSRSデータを渡す
                    update_srs_data(
                        q['page_id'], val, q['interval'], q['ease_factor'], q['reps']
                    )
                st.session_state.flash_index += 1
                st.session_state.flash_show_answer = False
                st.rerun()

if __name__ == "__main__":
    main()
    
