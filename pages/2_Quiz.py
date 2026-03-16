import streamlit as st
import random
# 1. 関数名を最新の Notion版 db_handler に合わせる
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

# 2. ページ設定は一番最初に実行
st.set_page_config(page_title="建築設備士クイズ", layout="wide")

def main():
    st.title("🧠 建築設備士 クイズ")

    # サイドバーでモード・分野を選択
    st.sidebar.header("⚙️ 設定")
    mode = st.sidebar.radio("学習モード", ["忘却曲線モード", "全問トレーニング"])
    
    section_map = {"7": "7_配管とポンプ", "8": "8_ダクトと送風機", "10": "10_排煙設備"}
    selected_sections = st.sidebar.multiselect("分野選択", options=list(section_map.values()), default=[])

    # 設定変更時に問題をリロード
    current_cfg = f"{mode}-{selected_sections}"
    if "last_cfg" not in st.session_state or st.session_state.last_cfg != current_cfg:
        if "questions" in st.session_state: del st.session_state.questions
        st.session_state.last_cfg = current_cfg

    # 3. データの取得
    if 'questions' not in st.session_state:
        try:
            with st.spinner("Notionから取得中..."):
                all_raw = get_notion_data()
                due_ids = get_due_questions()
                
                qs = []
                for item in all_raw:
                    p = item.get("properties", {})
                    # NotionのID列（タイトル）からIDを取得
                    id_list = p.get("id", {}).get("title", [])
                    qid = id_list[0].get("plain_text", "") if id_list else ""
                    if not qid: continue

                    prefix = qid.split('-')[0]
                    section_name = section_map.get(prefix, "その他")

                    # フィルタリング
                    if selected_sections and section_name not in selected_sections: continue
                    if mode == "忘却曲線モード" and qid not in due_ids: continue

                    # 辞書キーを db_handler の戻り値に合わせる
                    qs.append({
                        "page_id": item.get("id"),
                        "q_id": qid,
                        "question": p.get("question", {}).get("rich_text", [{}])[0].get("plain_text", "無題"),
                        "answer": p.get("answer", {}).get("rich_text", [{}])[0].get("plain_text", "無解答"),
                        "interval": p.get("interval", {}).get("number", 0) or 0,
                        "ease_factor": p.get("ease_factor", {}).get("number", 2.5) or 2.5,
                        "reps": p.get("reps", {}).get("number", 0) or 0
                    })
                
                random.shuffle(qs)
                st.session_state.questions = qs
                st.session_state.idx = 0
                st.session_state.ans = False
        except Exception as e:
            st.error(f"データ取得エラー: {e}")
            return

    if not st.session_state.questions:
        st.warning("該当する問題がありません。モードや分野を変えてみてください。")
        return

    # クイズ表示
    q = st.session_state.questions[st.session_state.idx]
    st.info(f"【{mode}】 問題 {st.session_state.idx + 1} / {len(st.session_state.questions)} (ID: {q['q_id']})")
    st.subheader(q["question"])

    if not st.session_state.ans:
        if st.button("答えを表示", type="primary"):
            st.session_state.ans = True
            st.rerun()
    else:
        st.success(f"**正解：** {q['answer']}")
        
        # 10_排煙設備.pdf などの参照表示
        ref = section_map.get(q['q_id'].split('-')[0], "関連資料")
        st.caption(f"📚 参照資料: {ref}")

        st.divider()
        cols = st.columns(4)
        for i, label in enumerate(["もう一度", "難しい", "普通", "簡単"]):
            if cols[i].button(label, key=f"q_btn_{i}"):
                update_srs_data(q['page_id'], i, q['interval'], q['ease_factor'], q['reps'])
                st.session_state.idx += 1
                st.session_state.ans = False
                st.rerun()

if __name__ == "__main__":
    main()
