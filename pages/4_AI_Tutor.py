import streamlit as st
from core.db_handler import call_gemini_api

st.set_page_config(page_title="AI Tutor", layout="wide")

def main():
    st.title("🤖 AI チューター")
    
    # 案内板
    st.info("""
    ### 📖 AIチューターの使い方
    1. **「2_Quiz」**で問題を解きます。
    2. 解説を読んでも分からない点があれば、このページに来てください。
    3. 下のチャット欄で、AIに質問を投げかけることができます。
    
    *※直前に表示していた問題の情報が自動的にAIに渡されます。*
    """)

    # セッション状態から現在の問題情報を取得
    current_q = st.session_state.get("current_question")
    
    if not current_q:
        st.warning("クイズ画面で問題を一度表示してから利用してください。")
        return

    st.markdown(f"**現在対象としている問題 ID:** `{current_q['q_id']}`")
    with st.expander("問題の内容を確認"):
        st.write(f"**問題文:** {current_q['question']}")
        for i, choice in enumerate(current_q['choices']):
            if choice:
                st.write(f"肢 {i+1}: {choice}")
                st.write(f"  *解説: {current_q['exps'][i]}*")
        st.write(f"**正解:** 肢 {current_q['answer']}")

    # チャット履歴の初期化
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # チャット履歴の表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ユーザー入力
    if prompt := st.chat_input("この肢がなぜ誤りなのか詳しく教えて"):
        # ユーザーメッセージを表示
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Gemini API の呼び出し
        with st.chat_message("assistant"):
            with st.spinner("AIが考えています..."):
                # コンテキストの構築
                context = f"""
あなたは建築設備士試験の専門講師です。受験生に対して、技術的な根拠に基づいた分かりやすい解説を提供してください。

【対象の問題】
問題文: {current_q['question']}

【各肢の内容と公式解説】
肢 1: {current_q['choices'][0]} (公式解説: {current_q['exps'][0]})
肢 2: {current_q['choices'][1]} (公式解説: {current_q['exps'][1]})
肢 3: {current_q['choices'][2]} (公式解説: {current_q['exps'][2]})
肢 4: {current_q['choices'][3]} (公式解説: {current_q['exps'][3]})

【正解】
肢 {current_q['answer']}

【ユーザーからの質問】
{prompt}
"""
                
                # 指示内容は call_gemini_api 内でプロンプトに結合されるため、空文字でも動作するが役割を強調
                system_instruction = "建築設備士の専門的な立場から、法規や技術基準を交えて、初心者にも理解しやすいように具体的に回答してください。"
                
                response = call_gemini_api(context, system_instruction)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
