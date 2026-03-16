import streamlit as st
import random
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

st.set_page_config(page_title="建築設備士クイズ", layout="wide")

def main():
    st.title("🧠 建築設備士 クイズ")

    # --- サイドバー設定 ---
    st.sidebar.header("⚙️ 学習設定")
    
    # 1. モード選択
    mode = st.sidebar.radio("学習モード", ["忘却曲線モード", "全問トレーニング"])
    
    # 分野の定義（IDの先頭数字と名称の対応）
    section_map = {
        "7": "7_配管とポンプ",
        "8": "8_ダクトと送風機",
        "10": "10_排煙設備"
    }
    
    # 2. 分野選択
    selected_section_names = st.sidebar.multiselect(
        "分野を選択（未選択で全分野）",
        options=list(section_map.values()),
        default=[]
    )
    
    # 設定が変更されたら問題をリロードさせるためのフック
    current_settings = f"{mode}-{selected_section_names}"
    if "last_settings" not in st.session_state or st.session_state.last_settings != current_settings:
        if "questions" in st.session_state:
            del st.session_state.questions
        st.session_state.last_settings = current_settings

    # --- データの取得とフィルタリング ---
    if 'questions' not in st.session_state:
        with st.spinner("Notionから最新データを取得中..."):
            all_raw = get_notion_data()
            due_ids = get_due_questions()
            
            qs = []
            for item in all_raw:
                p = item.get("properties", {})
                id_list = p.get("id", {}).get("title", [])
                qid = id_list[0].get("plain_text", "") if id_list else ""
                if not qid: continue

                # 分野の特定（IDの先頭を取得）
                prefix = qid.split('-')[0]
                section_name = section_map.get(prefix, "その他")

                # 分野フィルターの判定
                if selected_section_names and section_name not in selected_section_names:
                    continue

                # モードフィルターの判定
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

    # --- クイズ表示 ---
    if not st.session_state.questions:
        st.warning(f"該当する問題がありません。モード：{mode} / 選択分野：{selected_section_names}")
        return

    q = st.session_state.questions[st.session_state.idx]
    st.info(f"【{mode}】 問題 {st.session_state.idx + 1} / {len(st.session_state.questions)} (ID: {q['q_id']})")
    st.subheader(q["question"])

    if not st.session_state.ans:
        if st.button("答えを表示", type="primary"):
            st.session_state.ans = True
            st.rerun()
    else:
        st.success(f"**正解：** {q['answer']}")
        
        # 参照資料の動的表示
        prefix = q['q_id'].split('-')[0]
        ref_pdf = section_map.get(prefix, "関連PDF資料")
        st.caption(f"📚 参照資料: {ref_pdf}")

        st.divider()
        cols = st.columns(4)
        for i, label in enumerate(["もう一度", "難しい", "普通", "簡単"]):
            if cols[i].button(label, key=f"q_btn_{i}"):
                update_srs_data(q['page_id'], i, q['interval'], q['ease_factor'], q['reps'])
                st.session_state.idx += 1
                st.session_state.ans = False
                st.rerun()
