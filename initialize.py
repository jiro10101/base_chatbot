"""
このファイルは、最初の画面読み込み時にのみ実行される初期化処理が記述されたファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from uuid import uuid4
from dotenv import load_dotenv
import tiktoken
from langchain_openai import ChatOpenAI
import utils
import constants as ct



############################################################
# 設定関連
############################################################
load_dotenv()


############################################################
# 関数定義
############################################################

def initialize_app_data():
    """
    アプリケーション全体で共有するデータの初期化
    
    Returns:
        dict: 初期化されたアプリデータ
    """
    # ログ出力の設定
    initialize_logger()
    
    logger = logging.getLogger(ct.LOGGER_NAME)
    
    # セッションIDの生成
    session_id = uuid4().hex
    
    # 消費トークン数カウント用のオブジェクトを用意
    enc = tiktoken.get_encoding(ct.ENCODING_KIND)
    
    # LLMの初期化
    llm = ChatOpenAI(model_name=ct.MODEL, temperature=ct.TEMPERATURE, streaming=True)
    
    # シンプルなChainを作成（RAGなし）
    simple_chain = utils.create_simple_chain(llm)
    
    logger.info(f"アプリデータの初期化が完了しました - Session: {session_id}")
    
    return {
        "session_id": session_id,
        "enc": enc,
        "llm": llm,
        "simple_chain": simple_chain
    }


def initialize_logger():
    """
    ログ出力の設定
    """
    os.makedirs(ct.LOG_DIR_PATH, exist_ok=True)

    logger = logging.getLogger(ct.LOGGER_NAME)

    if logger.hasHandlers():
        return

    log_handler = TimedRotatingFileHandler(
        os.path.join(ct.LOG_DIR_PATH, ct.LOG_FILE),
        when="D",
        encoding="utf8"
    )
    formatter = logging.Formatter(
        f"[%(levelname)s] %(asctime)s line %(lineno)s, in %(funcName)s: %(message)s"
    )
    log_handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)


