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
        st.success("こちらはRedmineチケット文言案を生成するAIチャットボットです。画面下部のチャット欄からRedmine番号や要求を入力してください。")
    # 使用例の表示
    with st.expander("💡 使用例", expanded=False):
        st.markdown("""
        **Redmine番号を指定する場合:**
        - Redmine #12345 を参考に新しいチケットを作成して
        - #12345
        - チケット 12345 の内容で文言案を作成
        
        **直接依頼する場合:**
        - データベースのバックアップ手順のチケットを作成したい
        - 新機能のテストチケットの文言案を作って
        
        **注意:**
        Redmine番号を指定した場合、そのチケットの情報を取得して参考にします。
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

