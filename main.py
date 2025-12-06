"""
このファイルは、Webアプリのメイン処理が記述されたファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
from dotenv import load_dotenv
import logging
import streamlit as st
import utils
from initialize import initialize
import components as cn
import constants as ct


############################################################
# 設定関連
############################################################
st.set_page_config(
    page_title=ct.APP_NAME
)

load_dotenv()

logger = logging.getLogger(ct.LOGGER_NAME)


############################################################
# 初期化処理
############################################################
try:
    initialize()
except Exception as e:
    logger.error(f"{ct.INITIALIZE_ERROR_MESSAGE}\n{e}")
    st.error(utils.build_error_message(ct.INITIALIZE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    st.stop()

# アプリ起動時のログ出力
if not "initialized" in st.session_state:
    st.session_state.initialized = True
    logger.info(ct.APP_BOOT_MESSAGE)


############################################################
# 初期表示
############################################################
# タイトル表示
cn.display_app_title()

# AIメッセージの初期表示
cn.display_initial_ai_message()


############################################################
# スタイリング処理
############################################################
# 画面装飾を行う「CSS」を記述
st.markdown(ct.STYLE, unsafe_allow_html=True) #保留


############################################################
# チャット入力の受け付け
############################################################
chat_message = st.chat_input(ct.CHAT_INPUT_HELPER_TEXT)


############################################################
# 会話ログの表示
############################################################
try:
    cn.display_conversation_log(chat_message)
except Exception as e:
    logger.error(f"{ct.CONVERSATION_LOG_ERROR_MESSAGE}\n{e}")
    st.error(utils.build_error_message(ct.CONVERSATION_LOG_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    st.stop()


############################################################
# チャット送信時の処理
############################################################
if chat_message:
    # ==========================================
    # 会話履歴の上限を超えた場合、受け付けない
    # ==========================================
    # ユーザーメッセージのトークン数を取得
    input_tokens = len(st.session_state.enc.encode(chat_message))
    # トークン数が、受付上限を超えている場合にエラーメッセージを表示
    if input_tokens > ct.MAX_ALLOWED_TOKENS:
        with st.chat_message("assistant", avatar=ct.AI_ICON_FILE_PATH):
            st.error(ct.INPUT_TEXT_LIMIT_ERROR_MESSAGE)
            st.stop()
    # トークン数が受付上限を超えていない場合、会話ログ全体のトークン数に加算
    st.session_state.total_tokens += input_tokens

    # ==========================================
    # 1. ユーザーメッセージの表示
    # ==========================================
    logger.info({"message": chat_message})

    res_box = st.empty()
    with st.chat_message("user", avatar=ct.USER_ICON_FILE_PATH):
        st.markdown(chat_message)
    
    # ==========================================
    # 1.5. Redmine番号の検出と情報取得
    # ==========================================
    redmine_issue_id = utils.extract_redmine_issue_id(chat_message)
    if redmine_issue_id:
        with st.spinner(f"Redmineチケット #{redmine_issue_id} の情報を取得中..."):
            redmine_info_dict = utils.get_redmine_issue(redmine_issue_id)
            if redmine_info_dict:
                redmine_info = utils.format_redmine_info_for_prompt(redmine_info_dict)
                # Redmine情報を含めてChainを再作成
                st.session_state.simple_chain = utils.create_simple_chain(redmine_info)
                st.info(f"✅ Redmineチケット #{redmine_issue_id} の情報を取得しました")
            else:
                st.warning(f"⚠️ Redmineチケット #{redmine_issue_id} の情報を取得できませんでした")
    
    # ==========================================
    # 2. LLMからの回答取得 or 問い合わせ処理
    # ==========================================
    res_box = st.empty()
    try:
        with st.spinner(ct.SPINNER_TEXT):
            result = utils.execute_agent_or_chain(chat_message)
    except Exception as e:
        logger.error(f"{ct.MAIN_PROCESS_ERROR_MESSAGE}\n{e}")
        st.error(utils.build_error_message(ct.MAIN_PROCESS_ERROR_MESSAGE), icon=ct.ERROR_ICON)
        st.stop()
    
    # ==========================================
    # 3. 古い会話履歴を削除
    # ==========================================
    utils.delete_old_conversation_log(result)

    # ==========================================
    # 4. LLMからの回答表示
    # ==========================================
    with st.chat_message("assistant", avatar=ct.AI_ICON_FILE_PATH):
        try:
            cn.display_llm_response(result)

            logger.info({"message": result})
        except Exception as e:
            logger.error(f"{ct.DISP_ANSWER_ERROR_MESSAGE}\n{e}")
            st.error(utils.build_error_message(ct.DISP_ANSWER_ERROR_MESSAGE), icon=ct.ERROR_ICON)
            st.stop()
    
    # ==========================================
    # 5. 会話ログへの追加
    # ==========================================
    st.session_state.messages.append({"role": "user", "content": chat_message})
    st.session_state.messages.append({"role": "assistant", "content": result})


############################################################
# Redmineチケット作成ボタンの表示判定
############################################################
if "messages" in st.session_state and st.session_state.messages:
    last_msg = st.session_state.messages[-1]
    
    # 最後のメッセージがAIからのもので、かつチケットドラフトを含んでいる場合
    if last_msg["role"] == "assistant":
        draft_data = utils.parse_ticket_draft(last_msg["content"])
        
        if draft_data:
            st.divider()
            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button("Redmineにチケット作成", type="primary"):
                    with st.spinner("Redmineにチケットを作成しています..."):
                        # プロジェクトIDは環境変数から自動取得される
                        new_ticket_id = utils.create_redmine_issue(draft_data)
                        
                        if new_ticket_id:
                            st.success(f"✅ チケット #{new_ticket_id} を作成しました！")
                            logger.info(f"Ticket created: {new_ticket_id}")
                        else:
                            st.error("❌ チケット作成に失敗しました。ログを確認してください。")
            with col2:
                st.caption("※ 上記の内容でRedmineにチケットを作成します")



