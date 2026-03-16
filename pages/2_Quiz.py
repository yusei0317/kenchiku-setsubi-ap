import streamlit as st
import random
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

# 1. ページ設定は必ず最初に行う
st.set_page_config(page_title="建築設備士クイズ", layout="wide")

def main():
    st.title("🧠 建築設備士 クイズ")

    # サイドバーの設定
    st.sidebar.header("⚙️ 設定")
    mode = st.sidebar.radio("学習モード", ["忘却曲線モード", "全問トレーニング"])
    if st.sidebar.button("キャッシュをクリアして再読込"):
        if 'questions' in st.session_state:
            del st.session_state.questions
        st.rerun()

    # 2. データの取得とセッション管理
    try:
        if 'questions' not in st.session_state:
            with st.spinner("Notionから最新データを取得中..."):
                all_raw = get_notion_data()
                due_ids = get_due_questions()
                
                if not all_raw:
                    st.error("Notionからデータが取得できませんでした。SecretsまたはDBの権限を確認してください。")
                    return

                qs = []
                for item in all_raw:
                    p = item.get("properties", {})
                    # IDの安全な取得
                    id_list = p.get("id", {}).get("title", [])
                    qid = id_list[0].get("plain_text", "") if id_list else ""
                    
                    if not qid: continue

                    # モードによるフィルタリング
                    if mode == "全問トレーニング" or qid in due_ids:
                        qs.append({
                            "page_id": item.get("id"),
                            "q_id": qid,
                            "question": p.get("question", {}).get("rich_text", [{}])[0].get("plain_text", "問題文なし"),
                            "answer": p.get("answer", {}).get("rich_text", [{}])[0].get("plain_text", "解答なし"),
                            "interval": p.get("interval", {}).get("number", 0) or 0,
                            "ease_factor": p.get("ease_factor", {}).get("number", 2.5) or 2.5,
                            "reps": p.get("reps", {}).get("number", 0) or 0
                        })
                
                random.shuffle(qs)
                st.session_state.questions = qs
                st.session_state.idx = 0
                st.session_state.ans = False

        if not st.session_state.questions:
            st.warning("🎉 現在、復習が必要な問題はありません。サイドバーで「全問トレーニング」に切り替えてみてください。")
            return

        # 3. クイズ表示
        q = st.session_state.questions[st.session_state.idx]
        st.info(f"【{mode}】 問題 {st.session_state.idx + 1} / {len(st.session_state.questions)} (ID: {q['q_id']})")
        
        st.subheader(q["question"])

        if not st.session_state.ans:
            if st.button("答えを表示", type="primary"):
                st.session_state.show_ans_internal = True # 内部状態
                st.session_state.ans = True
                st.rerun()
        else:
            st.success(f"**正解：** {q['answer']}")
            
            # PDFマッピング
            pdf_prefix = q['q_id'].split('-')[0] if '-' in q['q_id'] else ""
            pdf_name = {"10": "10_排煙設備.pdf", "8": "8_ダクトと送風機.pdf", "7": "7_配管とポンプ.pdf"}.get(pdf_prefix, "関連PDF")
            st.caption(f"📚 参照資料: {pdf_name}")

            st.divider()
            cols = st.columns(4)
            labels = [("もう一度", 0), ("難しい", 1), ("普通", 2), ("簡単", 3)]
            for i, (label, val) in enumerate(labels):
                if cols[i].button(label, key=f"q_btn_{i}"):
                    # ここで新しい関数名 update_srs_data を使用
                    update_srs_data(q['page_id'], val, q['interval'], q['ease_factor'], q['reps'])
                    st.session_state.idx += 1
                    st.session_state.ans = False
                    st.rerun()

    except Exception as e:
        st.error(f"クイズ実行中にエラーが発生しました: {e}")
        st.info("一度『キャッシュをクリア』ボタンを押してみてください。")

if __name__ == "__main__":
    main()
