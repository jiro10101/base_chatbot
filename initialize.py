"""
アプリ起動時（画面の初回読み込み時）にのみ実行される初期化処理を定義するファイル。
Streamlit はページ再描画のたびにスクリプト全体を再実行するため、
session_state の有無をチェックして二重初期化を防ぐ。
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from uuid import uuid4
import streamlit as st
import tiktoken
from langchain_openai import ChatOpenAI
import utils
import constants as ct


def initialize():
    """アプリ起動時に必要な初期化処理をまとめて実行する"""
    initialize_session_state()
    initialize_session_id()
    initialize_logger()
    initialize_llm_chain()


def initialize_session_state():
    """
    session_state の初期値をセットする。
    すでに初期化済みの場合は何もしない（再描画時の上書き防止）。

    - messages      : 画面表示用の会話ログ（role/content の辞書リスト）
    - chat_history  : LangChain に渡す会話履歴（HumanMessage/AIMessage のリスト）
    - total_tokens  : 会話履歴の累計トークン数（上限管理用）
    - current_command: チャットから抽出した最新の有効コマンド
    - exec_result   : Screen 実行の結果（サイドバー表示用）
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.session_state.total_tokens = 0
        st.session_state.current_command = None
        st.session_state.exec_result = None


def initialize_session_id():
    """ログ出力用のセッションIDを生成する（セッションをまたいで追跡するため）"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid4().hex


def initialize_logger():
    """
    日次ローテーションのファイルロガーを設定する。
    ハンドラーが既に存在する場合はスキップ（Streamlit 再描画時の重複登録防止）。
    ログ出力先: {LOG_DIR_PATH}/application.log
    """
    os.makedirs(ct.LOG_DIR_PATH, exist_ok=True)

    logger = logging.getLogger(ct.LOGGER_NAME)
    if logger.hasHandlers():
        return  # 既にセットアップ済み

    log_handler = TimedRotatingFileHandler(
        os.path.join(ct.LOG_DIR_PATH, ct.LOG_FILE),
        when="D",        # D = 日次でローテーション
        encoding="utf8"
    )
    formatter = logging.Formatter(
        f"[%(levelname)s] %(asctime)s line %(lineno)s, in %(funcName)s, session_id={st.session_state.session_id}: %(message)s"
    )
    log_handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)


def initialize_llm_chain():
    """
    LLM（ChatOpenAI）とトークンカウンター（tiktoken）を初期化し、
    LangChain LCEL パイプラインを構築して session_state に保存する。
    """
    # トークン数カウント用エンコーダー（会話履歴の上限管理に使用）
    st.session_state.enc = tiktoken.get_encoding(ct.ENCODING_KIND)
    st.session_state.llm = ChatOpenAI(model_name=ct.MODEL, temperature=ct.TEMPERATURE, streaming=True)
    # Chain は LLM に依存するため、LLM 生成後に構築する
    st.session_state.simple_chain = utils.create_simple_chain()
