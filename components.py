"""
このファイルは、画面表示に特化した関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import logging
import streamlit as st
import constants as ct


############################################################
# 関数定義
############################################################

def display_app_title():
    """
    タイトル表示
    """
    st.markdown(f"## {ct.APP_NAME}")



def display_initial_ai_message():
    """
    AIメッセージの初期表示
    """
    with st.chat_message("assistant", avatar=ct.AI_ICON_FILE_PATH):
        st.success("わかる条件だけ伝えてくれれば、AIがスクリプトの候補を作ります。")
    # 使用例の表示
    with st.expander("💡 使用例", expanded=False):
        st.markdown("""
        各試験を実施するために必要条件を指定、スクリプトを作成します。
        1.  **FWVer** [試験対象のFWVer]: 例 `1.00`, `1.20`, `1.04`
        2.  **Model** [試験対象の気象]:例   `ModelA`, `ModelB`, `ModelC`
        3.  **Testscript** [試験スクリプト名]: 例  `rand_read_simple.sh`, `rand_write_simple.sh`, `seq_read_simple.sh`, `seq_write_simple.sh`
        4.  **TestingEnvironment** [試験環境]: 例  `100.67.161.104`, `192.168.20.20`
        5.  **Testtool** [試験ツールのVer]: 例  `r3`, `r5`, `r2`

        実行例1：全条件を指定
        ユーザー: Testtool: r3, FWVer: 1.20, Testscript: seq_read_simple.sh, Model: ModelA で。
        AI: Testtoolsqript_r3 1.20 seq_read_simple.sh ModelA

        """)

def display_conversation_log(chat_message):
    """
    会話ログの一覧表示
    """
    # 会話ログの最後を表示する時のみ、フィードバック後のメッセージ表示するために「何番目のメッセージか」を取得
    for index, message in enumerate(st.session_state.messages):
        if message["role"] == "assistant":
            with st.chat_message(message["role"], avatar=ct.AI_ICON_FILE_PATH):
                st.markdown(message["content"])
        else:
            with st.chat_message(message["role"], avatar=ct.USER_ICON_FILE_PATH):
                st.markdown(message["content"])




def display_llm_response(result):
    """
    LLMからの回答表示

    Args:
        result: LLMからの回答
    """
    st.markdown(result)

