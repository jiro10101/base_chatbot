"""
Streamlit アプリのエントリーポイント。
Streamlit はページ操作のたびにこのファイルを先頭から再実行するため、
初期化処理は session_state の有無で制御している。

処理フロー:
  1. 初期化（LLM・ロガー・session_state）
  2. 画面の初期描画（タイトル・AIメッセージ・会話ログ）
  3. チャット送信時: コマンド検証 → LLM応答 → サイドバー更新
"""

from dotenv import load_dotenv
import logging
import streamlit as st
import utils
from initialize import initialize
import components as cn
import constants as ct

st.set_page_config(page_title=ct.APP_NAME)

# .env から OPENAI_API_KEY などの環境変数を読み込む
load_dotenv()

logger = logging.getLogger(ct.LOGGER_NAME)

# --- 初期化処理 ---
try:
    initialize()
except Exception as e:
    logger.error(f"{ct.INITIALIZE_ERROR_MESSAGE}\n{e}")
    st.error(utils.build_error_message(ct.INITIALIZE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    st.stop()

# アプリ起動ログは初回のみ出力（再描画時はスキップ）
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    logger.info(ct.APP_BOOT_MESSAGE)

# --- 初期描画 ---
cn.display_app_title()
cn.display_initial_ai_message()
st.markdown(ct.STYLE, unsafe_allow_html=True)

# --- チャット入力 ---
# chat_input は送信されたときのみ文字列、それ以外は None を返す
chat_message = st.chat_input(ct.CHAT_INPUT_HELPER_TEXT)

# --- 会話ログ表示 ---
try:
    cn.display_conversation_log(chat_message)
except Exception as e:
    logger.error(f"{ct.CONVERSATION_LOG_ERROR_MESSAGE}\n{e}")
    st.error(utils.build_error_message(ct.CONVERSATION_LOG_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    st.stop()

# --- チャット送信時の処理 ---
if chat_message:
    # 入力トークン数チェック（上限超過なら受け付けない）
    input_tokens = len(st.session_state.enc.encode(chat_message))
    if input_tokens > ct.MAX_ALLOWED_TOKENS:
        with st.chat_message("assistant", avatar=ct.AI_ICON_FILE_PATH):
            st.error(ct.INPUT_TEXT_LIMIT_ERROR_MESSAGE)
            st.stop()
    st.session_state.total_tokens += input_tokens

    logger.info({"message": chat_message})

    with st.chat_message("user", avatar=ct.USER_ICON_FILE_PATH):
        st.markdown(chat_message)

    try:
        with st.spinner(ct.SPINNER_TEXT):
            # ユーザー入力が正規コマンドの場合はそのまま確認メッセージを生成（LLM不使用）
            # 正規コマンドでない場合はLLMにコマンド候補の生成を依頼
            validation_result = utils.validate_command_format(chat_message)
            if validation_result["valid"]:
                result = f"✓ コマンドの形式が正しいです。\n\nコマンド: `{validation_result['command']}`\n\n「Screen実行」ボタンで実行できます。"
                st.session_state.current_command = validation_result["command"]
                st.session_state.exec_result = None  # コマンドが入力されるたびに実行結果をリセット（再試験可能）
            else:
                result = utils.execute_agent_or_chain(chat_message)
    except Exception as e:
        logger.error(f"{ct.MAIN_PROCESS_ERROR_MESSAGE}\n{e}")
        st.error(utils.build_error_message(ct.MAIN_PROCESS_ERROR_MESSAGE), icon=ct.ERROR_ICON)
        st.stop()

    utils.delete_old_conversation_log(result)

    with st.chat_message("assistant", avatar=ct.AI_ICON_FILE_PATH):
        try:
            cn.display_llm_response(result)

            # LLM応答にもコマンドが含まれる場合（LLMがコマンドを生成した場合）も current_command を更新
            validation_result = utils.validate_command_format(result)
            if validation_result["valid"]:
                st.session_state.current_command = validation_result["command"]
                st.session_state.exec_result = None  # コマンドが生成されるたびに実行結果をリセット（再試験可能）

            logger.info({"message": result})
        except Exception as e:
            logger.error(f"{ct.DISP_ANSWER_ERROR_MESSAGE}\n{e}")
            st.error(utils.build_error_message(ct.DISP_ANSWER_ERROR_MESSAGE), icon=ct.ERROR_ICON)
            st.stop()

    # 表示用ログと LangChain 用履歴は別系統で管理している
    # messages: 画面描画用（role/content の辞書）
    # chat_history: LangChain に渡す用（execute_agent_or_chain 内で更新済み）
    st.session_state.messages.append({"role": "user", "content": chat_message})
    st.session_state.messages.append({"role": "assistant", "content": result})

# --- サイドバー表示（再描画のたびに最新 session_state で描画） ---
cn.display_sidebar()
