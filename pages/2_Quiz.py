import streamlit as st
import random
from core.db_handler import get_notion_data, update_srs_data, get_due_questions

# 1. ページ設定
st.set_page_config(page_title="建築設備士 択一クイズ", layout="wide")

def main():
    st.title("🧠 建築設備士 択一クイズ")

    # サイドバー設定
    st.sidebar.header("⚙️ 学習設定")
    mode = st.sidebar.radio("学習モード", ["忘却曲線モード", "全問トレーニング"])
    
    # 分野マップ（IDの接頭辞に対応）
    section_map = {"7": "7_配管とポンプ", "8": "8_ダクトと送風機", "10": "10_排煙設備"}
    selected_sections = st.sidebar.multiselect("分野を選択（未選択で全分野）", options=list(section_map.values()))

    # 設定変更時に問題をリロード
    current_cfg = f"{mode}-{selected_sections}"
    if "last_cfg" not in st.session_state or st.session_state.last_cfg != current_cfg:
        if "questions" in st.session_state:
            del st.session_state.questions
        st.session_state.last_cfg = current_cfg

    # データの取得とフィルタリング
    if 'questions' not in st.session_state:
        with st.spinner("Notionから最新データを取得中..."):
            all_data = get_notion_data()
            due_ids = get_due_questions()
            
            qs = []
            for q in all_data:
                # 分野フィルター
                prefix = q['q_id'].split('_')[0] if '_' in q['q_id'] else q['q_id'][:1]
                # 配管ポンプ_001 のような形式なら「配管ポンプ」で判定
                current_section = section_map.get(prefix.replace("配管ポンプ", "7").replace("排煙", "10"), "その他")
                
                if selected_sections and current_section not in selected_sections:
                    continue
                # モードフィルター
                if mode == "忘却曲線モード" and q['q_id'] not in due_ids:
                    continue
                qs.append(q)
            
            random.shuffle(qs)
            st.session_state.questions = qs
            st.session_state.idx = 0
            st.session_state.ans = False

    if not st.session_state.questions:
        st.warning("該当する問題がありません。モードや分野を変えてみてください。")
        return

    # 現在の問題を取得
    q = st.session_state.questions[st.session_state.idx]
    st.info(f"【{mode}】 問題 {st.session_state.idx + 1} / {len(st.session_state.questions)} (ID: {q['q_id']})")
    st.subheader(q["question"])

    # --- 回答フェーズ ---
    if not st.session_state.ans:
        # 選択肢のリスト作成（空文字除外）
        choices = [c for c in q["choices"] if c]
        if not choices:
            st.error("選択肢(choice_1~4)が見つかりません。Notionの列名を確認してください。")
            return
            
        user_choice = st.radio("最も不適当なもの（または適当なもの）を選んでください：", choices, index=None)
        
        if st.button("回答を確定", type="primary"):
            if user_choice:
                st.session_state.selected = user_choice
                st.session_state.ans = True
                st.rerun()
            else:
                st.warning("選択肢を選んでください。")
                
    # --- 解説フェーズ ---
    else:
        # 正解番号の安全な数値変換（ValueError対策）
        ans_str = str(q["answer"]).strip()
        if ans_str.isdigit():
            correct_idx = int(ans_str) - 1
            correct_text = q["choices"][correct_idx] if 0 <= correct_idx < len(q["choices"]) else "不明"
        else:
            st.error(f"正解データ形式エラー: {ans_str}")
            correct_text = "不明"

        # 正否判定の表示
        if st.session_state.selected == correct_text:
            st.success(f"⭕ 正解！ 正解は肢 {ans_str} です。")
        else:
            st.error(f"❌ 不正解... 正解は肢 {ans_str} です。")
            st.write(f"あなたの選択： {st.session_state.selected}")

        # 各肢の詳細解説を表示
        st.markdown("### 📝 各肢の解説")
        for i in range(4):
            choice_text = q["choices"][i]
            exp_text = q["exps"][i]
            if not choice_text: continue
            
            # 正解の肢（不適当な肢）を強調
            label = f"肢 {i+1}"
            if i == correct_idx:
                label = f"🎯 {label} (不適当)"
            
            with st.expander(f"{label}: {choice_text[:40]}...", expanded=(i == correct_idx)):
                st.write(f"**内容:** {choice_text}")
                st.write(f"**解説:** {exp_text}")

        # 画像の表示
        if q["image_url"]:
            st.divider()
            st.image(q["image_url"], caption=f"解説図解: {q['q_id']}")

        st.divider()
        st.write("今回の暗記度は？（忘却曲線データを更新します）")
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
