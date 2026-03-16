import streamlit as st
import random
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

# 1. ページ設定（UIの基本）
st.set_page_config(page_title="建築設備士 択一クイズ", layout="wide")

def main():
    st.title("🧠 建築設備士 択一クイズ")

    # --- サイドバー：学習条件の設定 ---
    st.sidebar.header("⚙️ 学習設定")
    mode = st.sidebar.radio("学習モード", ["忘却曲線モード", "全問トレーニング"])
    
    # 分野の定義（IDに基づいた自動振り分け）
    section_map = {"配管ポンプ": "7_配管とポンプ", "ダクト": "8_ダクトと送風機", "排煙": "10_排煙設備"}
    selected_sections = st.sidebar.multiselect("分野を選択（未選択で全分野）", options=list(section_map.values()))

    # 設定が変更されたらセッションをリセットして再読込
    current_cfg = f"{mode}-{selected_sections}"
    if "last_cfg" not in st.session_state or st.session_state.last_cfg != current_cfg:
        if "questions" in st.session_state:
            del st.session_state.questions
        st.session_state.last_cfg = current_cfg

    # --- データの読み込み ---
    if 'questions' not in st.session_state:
        with st.spinner("Notionから最新データを取得中..."):
            try:
                all_data = get_notion_data()
                due_ids = get_due_questions()
                
                # フィルタリングロジック
                qs = []
                for q in all_data:
                    prefix = q['q_id'].split('_')[0]
                    section_name = section_map.get(prefix, "その他")
                    
                    if selected_sections and section_name not in selected_sections:
                        continue
                    if mode == "忘却曲線モード" and q['q_id'] not in due_ids:
                        continue
                    qs.append(q)
                
                random.shuffle(qs)
                st.session_state.questions = qs
                st.session_state.idx = 0
                st.session_state.ans = False
            except Exception as e:
                st.error(f"データの読み込み中にエラーが発生しました: {e}")
                return

    if not st.session_state.questions:
        st.warning("該当する問題がありません。モードや分野を変えてみてください。")
        return

    # 現在の問題をセット
    q = st.session_state.questions[st.session_state.idx]
    
    # --- UI表示：問題パート ---
    st.info(f"【{mode}】 問題 {st.session_state.idx + 1} / {len(st.session_state.questions)} (ID: {q['q_id']})")
    
    st.markdown("### 問題文")
    st.subheader(q["question"])

    # 回答前：選択肢提示
    if not st.session_state.ans:
        choices = [c for c in q["choices"] if c]
        if not choices:
            st.error("選択肢データ(choice_1~4)が読み込めませんでした。")
            return
            
        user_choice = st.radio("最も不適当なもの（または適当なもの）を選んでください：", choices, index=None)
        
        if st.button("回答を確定", type="primary"):
            if user_choice:
                st.session_state.selected = user_choice
                st.session_state.ans = True
                st.rerun()
            else:
                st.warning("選択肢を選んでください。")
                
    # 回答後：結果と解説
    else:
        # 正解番号の安全な解析
        ans_raw = str(q["answer"]).strip()
        correct_idx = int(ans_raw) - 1 if ans_raw.isdigit() else -1
        
        if correct_idx >= 0 and st.session_state.selected == q["choices"][correct_idx]:
            st.success(f"⭕ 正解！ 正解は肢 {ans_raw} です。")
        else:
            st.error(f"❌ 不正解... 正解は肢 {ans_raw} です。")
            st.write(f"あなたの回答： {st.session_state.selected}")

        # 解説図解（視覚情報を最優先）
        if q["image_url"]:
            st.divider()
            st.image(q["image_url"], caption=f"解説図解: {q['q_id']}")

        # --- 肢別解説（デフォルトで閉じる設定） ---
        st.markdown("---")
        st.markdown("### 📝 肢別詳細解説")
        for i in range(4):
            choice_text = q["choices"][i]
            if not choice_text: continue
            
            label = f"肢 {i+1}"
            is_correct_branch = (i == correct_idx)
            if is_correct_branch:
                label = f"🎯 {label} (不適当/適当な肢)"
            
            # expanded=False でデフォルトで閉じた状態にする
            with st.expander(f"{label}: {choice_text[:40]}...", expanded=False):
                st.write(f"**内容:** {choice_text}")
                st.markdown(f"**解説:** {q['exps'][i]}")

        # --- SRS評価ボタン ---
        st.divider()
        st.write("今回の暗記度は？（忘却曲線データを更新します）")
        cols = st.columns(4)
        labels = ["もう一度", "難しい", "普通", "簡単"]
        for i, label in enumerate(labels):
            if cols[i].button(label, key=f"srs_btn_{i}"):
                update_srs_data(q['page_id'], i, q['interval'], q['ease_factor'], q['reps'])
                st.session_state.idx += 1
                st.session_state.ans = False
                st.rerun()

if __name__ == "__main__":
    main()
