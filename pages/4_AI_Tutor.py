import streamlit as st
from core.db_handler import call_gemini_api

st.set_page_config(page_title="AI Tutor", layout="wide")

def main():
    st.title("🤖 AI チューター")
    
    # 案内板
    st.info("""
    ### 📖 AIチューターの使い方
    1. **「2_Quiz」**で問題を解きます。
    2. 解答後に「詳細解説」を読んでも腑に落ちない点があれば、このページに来てください。
    3. AIが問題の文脈を理解した状態で、技術的根拠に基づいた深掘り解説を行います。
    """)

    # セッション状態から現在の問題情報を取得
    current_q = st.session_state.get("current_question")
    
    if not current_q:
        st.warning("クイズ画面で問題を一度表示してから利用してください。")
        return

    st.markdown(f"**現在対象としている問題 ID:** `{current_q['q_id']}`")
    with st.expander("対象問題のコンテキストを確認"):
        st.write(f"**問題文:** {current_q['question']}")
        for i, choice in enumerate(current_q['choices']):
            if choice:
                st.write(f"肢 {i+1}: {choice}")
                st.write(f"  *公式解説: {current_q['exps'][i]}*")
        st.write(f"**正解:** 肢 {current_q['answer']}")

    # チャット履歴の初期化
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # チャット履歴の表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ユーザー入力
    if prompt := st.chat_input("この選択肢がなぜ正しいのか、より実務的な視点で教えて"):
        # ユーザーメッセージを表示
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Gemini API の呼び出し
        with st.chat_message("assistant"):
            with st.spinner("建築設備士講師が回答を生成中..."):
                # コンテキストの構築
                context = f"""
あなたは建築設備士試験のベテラン講師です。受験生に対して、単なる正誤だけでなく「なぜその理論が成り立つのか」「実務や法規ではどう扱われるか」といった深い理解を促す解説を行ってください。

【対象の問題データ】
問題文: {current_q['question']}

【選択肢と公式解説】
1: {current_q['choices'][0]} (解説: {current_q['exps'][0]})
2: {current_q['choices'][1]} (解説: {current_q['exps'][1]})
3: {current_q['choices'][2]} (解説: {current_q['exps'][2]})
4: {current_q['choices'][3]} (解説: {current_q['exps'][3]})

【正解】
肢 {current_q['answer']}

【受験生からの質問】
{prompt}
"""
                
                # 指示内容は call_gemini_api 内で冒頭に統合されます
                system_instruction = "建築設備の技術基準、法令（建築基準法、消防法等）、空気調和・給排水衛生・電気設備の専門知識を用いて、論理的かつ分かりやすく回答してください。"
                
                response = call_gemini_api(context, system_instruction)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
