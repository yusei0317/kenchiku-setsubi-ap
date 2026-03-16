import streamlit as st
import random
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

# 1. ページ設定
st.set_page_config(page_title="建築設備士 択一クイズ", layout="wide")

def main():
    st.title("🧠 建築設備士 択一クイズ")

    # --- サイドバー設定 ---
    st.sidebar.header("⚙️ 学習設定")
    mode = st.sidebar.radio("学習モード", ["忘却曲線モード", "全問トレーニング"])
    
    section_map = {"配管ポンプ": "7_配管とポンプ", "ダクト": "8_ダクトと送風機", "排煙": "10_排煙設備"}
    selected_sections = st.sidebar.multiselect("分野を選択", options=list(section_map.values()))

    # 設定変更検知
    current_cfg = f"{mode}-{selected_sections}"
    if "last_cfg" not in st.session_state or st.session_state.last_cfg != current_cfg:
        if "questions" in st.session_state:
            del st.session_state.questions
        st.session_state.last_cfg = current_cfg

    # --- データ取得 ---
    if 'questions' not in st.session_state:
        with st.spinner("Notionから最新データを取得中..."):
            try:
                all_data = get_notion_data()
                due_ids = get_due_questions()
                
                qs = []
                for q in all_data:
                    prefix = q['q_id'].split('_')[0]
                    section_name = section_map.get(prefix, "その他")
                    if selected_sections and section_name not in selected_sections: continue
                    if mode == "忘却曲線モード" and q['q_id'] not in due_ids: continue
                    qs.append(q)
                
                random.shuffle(qs)
                st.session_state.questions = qs
                st.session_state.idx = 0
                st.session_state.ans = False
            except Exception as e:
                st.error(f"データ取得エラー: {e}")
                return

    if not st.session_state.questions:
        st.warning("該当する問題がありません。")
        return

    q = st.session_state.questions[st.session_state.idx]
    
    # --- 問題表示部（常に表示） ---
    st.info(f"【{mode}】 問題 {st.session_state.idx + 1} / {len(st.session_state.questions)} (ID: {q['q_id']})")
    st.markdown("### 📋 問題文")
    st.subheader(q["question"])

    # 回答フェーズ
    if not st.session_state.ans:
        choices = [c for c in q["choices"] if c]
        if not choices:
            st.error("選択肢データが読み込めませんでした。")
            return
            
        user_choice = st.radio("最も不適当なものを選んでください：", choices, index=None)
        
        if st.button("回答を確定", type="primary"):
            if user_choice:
                st.session_state.selected = user_choice
                st.session_state.ans = True
                st.rerun()
            else:
                st.warning("選択肢を選んでください。")
                
    # 解説フェーズ（折りたたまず全表示）
    else:
        ans_raw = str(q["answer"]).strip()
        correct_idx = int(ans_raw) - 1 if ans_raw.isdigit() else -1
        
        # 結果表示
        if correct_idx >= 0 and st.session_state.selected == q["choices"][correct_idx]:
            st.success(f"⭕ 正解！ 正解は肢 {ans_raw} です。")
        else:
            st.error(f"❌ 不正解... 正解は肢 {ans_raw} です。")
            st.write(f"あなたの選択： {st.session_state.selected}")

        # 図解画像
        if q["image_url"]:
            st.divider()
            st.image(q["image_url"], caption=f"解説図解: {q['q_id']}")

        # --- 肢別解説（expanded=Trueで全て開いた状態にする） ---
        st.markdown("---")
        st.markdown("### 📝 各肢の根拠と詳細解説")
        for i in range(4):
            choice_text = q["choices"][i]
            if not choice_text: continue
            
            label = f"肢 {i+1}"
            if i == correct_idx:
                label = f"🎯 {label} (正解/不適当な肢)"
            
            # expanded=True により最初から開いた状態で表示
            with st.expander(label, expanded=True):
                st.markdown(f"**【記述内容】**\n{choice_text}")
                st.markdown(f"**【解説】**\n{q['exps'][i]}")

        # SRS評価
        st.divider()
        st.write("暗記度を選択：")
        cols = st.columns(4)
        labels = ["もう一度", "難しい", "普通", "簡単"]
        for i, label in enumerate(labels):
            if cols[i].button(label, key=f"srs_{i}"):
                update_srs_data(q['page_id'], i, q['interval'], q['ease_factor'], q['reps'])
                st.session_state.idx += 1
                st.session_state.ans = False
                st.rerun()

if __name__ == "__main__":
    main()
