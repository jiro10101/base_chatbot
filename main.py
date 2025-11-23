"""
このファイルは、Webアプリのメイン処理が記述されたファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
from dotenv import load_dotenv
import logging
from taipy.gui import Gui, State, invoke_callback, get_state_id
import utils
from initialize import initialize_app_data
import components as cn
import constants as ct


############################################################
# 設定関連
############################################################
load_dotenv()

logger = logging.getLogger(ct.LOGGER_NAME)


############################################################
# グローバルデータの初期化
############################################################
# アプリ全体のデータを初期化
app_data = initialize_app_data()


############################################################
# ページマークダウン定義
############################################################
page = f"""
# {ct.APP_NAME}

<|part|class_name=chat-container|
{cn.get_initial_message()}

<|{{conversation}}|>

<|layout|columns=1 1|
<|{{user_message}}|input|label=メッセージを入力|on_change=send_message|class_name=chat-input|>
<|送信|button|on_action=send_message|class_name=send-button|>
|>
|>

<style>
.chat-container {{
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}}
.chat-input {{
    width: 100%;
}}
.send-button {{
    margin-left: 10px;
}}
.user-message {{
    background-color: #e3f2fd;
    padding: 10px;
    border-radius: 10px;
    margin: 10px 0;
    text-align: right;
}}
.assistant-message {{
    background-color: #f5f5f5;
    padding: 10px;
    border-radius: 10px;
    margin: 10px 0;
}}
.spinner {{
    text-align: center;
    padding: 10px;
    color: #666;
}}
</style>
"""


############################################################
# 状態変数の初期化
############################################################
conversation = ""
user_message = ""
messages = []
chat_history = []
total_tokens = 0
llm = None
simple_chain = None
enc = None
session_id = ""


############################################################
# コールバック関数
############################################################
def on_init(state: State):
    """
    状態の初期化（各ユーザーセッションごとに実行）
    """
    try:
        # グローバルデータから状態を初期化
        state.messages = []
        state.chat_history = []
        state.total_tokens = 0
        state.conversation = ""
        state.user_message = ""
        
        # グローバルデータから取得
        state.llm = app_data["llm"]
        state.simple_chain = app_data["simple_chain"]
        state.enc = app_data["enc"]
        state.session_id = app_data["session_id"]
        
        logger.info(f"{ct.APP_BOOT_MESSAGE} - Session: {state.session_id}")
    except Exception as e:
        logger.error(f"{ct.INITIALIZE_ERROR_MESSAGE}\n{e}")
        state.conversation = f"\n\n❌ **エラー:** {utils.build_error_message(ct.INITIALIZE_ERROR_MESSAGE)}\n\n---\n\n"


def send_message(state: State):
    """
    メッセージ送信処理
    """
    if not state.user_message or state.user_message.strip() == "":
        return
    
    chat_message = state.user_message.strip()
    state.user_message = ""  # 入力欄をクリア
    
    try:
        # トークン数チェック
        input_tokens = len(state.enc.encode(chat_message))
        if input_tokens > ct.MAX_ALLOWED_TOKENS:
            state.conversation += f"\n\n❌ **エラー:** {ct.INPUT_TEXT_LIMIT_ERROR_MESSAGE}\n\n---\n\n"
            return
        
        state.total_tokens += input_tokens
        
        # ユーザーメッセージを表示
        state.conversation += f"\n\n**あなた:** {chat_message}\n\n"
        logger.info({"message": chat_message, "session_id": state.session_id})
        
        # ローディング表示
        state.conversation += "*回答生成中...*\n\n"
        
        # LLMからの回答取得
        result = utils.execute_agent_or_chain(chat_message, state)
        
        # ローディングを削除
        state.conversation = state.conversation.replace("*回答生成中...*\n\n", "")
        
        # 古い会話履歴を削除
        utils.delete_old_conversation_log(result, state)
        
        # LLMの回答を表示
        state.conversation += f"**AI:** `{result}`\n\n---\n\n"
        logger.info({"message": result, "session_id": state.session_id})
        
        # 会話ログに追加
        state.messages.append({"role": "user", "content": chat_message})
        state.messages.append({"role": "assistant", "content": result})
        
    except Exception as e:
        logger.error(f"{ct.MAIN_PROCESS_ERROR_MESSAGE}\n{e}")
        state.conversation += f"\n\n❌ **エラー:** {utils.build_error_message(ct.MAIN_PROCESS_ERROR_MESSAGE)}\n\n---\n\n"


############################################################
# アプリケーション起動
############################################################
if __name__ == "__main__":
    gui = Gui(page)
    gui.run(
        host="0.0.0.0",
        port=8501,
        title=ct.APP_NAME,
        dark_mode=False,
        on_init=on_init
    )

