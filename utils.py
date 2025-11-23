"""
このファイルは、画面表示以外の様々な関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import os
from dotenv import load_dotenv
import logging
import sys
import unicodedata
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from typing import List
import constants as ct


############################################################
# 設定関連
############################################################
load_dotenv()


############################################################
# 関数定義
############################################################

def build_error_message(message):
    """
    エラーメッセージと管理者問い合わせテンプレートの連結

    Args:
        message: 画面上に表示するエラーメッセージ

    Returns:
        エラーメッセージと管理者問い合わせテンプレートの連結テキスト
    """
    return "\n".join([message, ct.COMMON_ERROR_MESSAGE])


def create_simple_chain(llm):
    """
    RAGを使用しない、シンプルな会話Chainを作成

    Args:
        llm: ChatOpenAIのインスタンス

    Returns:
        会話Chain
    """
    logger = logging.getLogger(ct.LOGGER_NAME)

    # RAGなしのシンプルなプロンプトテンプレート
    question_answer_template = ct.SYSTEM_PROMPT_INQUIRY
    question_answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", question_answer_template),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # LLMとプロンプトを組み合わせたチェーンを作成
    chain = question_answer_prompt | llm | StrOutputParser()
    
    # 入力形式を統一するためのラッパー
    def wrapped_chain(self, inputs):
        return {
            "answer": chain.invoke({
                "input": inputs["input"],
                "chat_history": inputs.get("chat_history", [])
            })
        }
    
    return type('SimpleChain', (), {'invoke': wrapped_chain})()


def delete_old_conversation_log(result, state):
    """
    古い会話履歴の削除

    Args:
        result: LLMからの回答
        state: Taipyのステート
    """
    # LLMからの回答テキストのトークン数を取得
    response_tokens = len(state.enc.encode(result))
    # 過去の会話履歴の合計トークン数に加算
    state.total_tokens += response_tokens

    # トークン数が上限値を下回るまで、順に古い会話履歴を削除
    while state.total_tokens > ct.MAX_ALLOWED_TOKENS:
        if len(state.chat_history) > 1:
            # 最も古い会話履歴を削除
            removed_message = state.chat_history.pop(0)
            # 最も古い会話履歴のトークン数を取得
            removed_tokens = len(state.enc.encode(removed_message.content))
            # 過去の会話履歴の合計トークン数から、最も古い会話履歴のトークン数を引く
            state.total_tokens -= removed_tokens
        else:
            break


def execute_agent_or_chain(chat_message, state):
    """
    シンプルなChainを実行

    Args:
        chat_message: ユーザーメッセージ
        state: Taipyのステート
    
    Returns:
        LLMからの回答
    """
    logger = logging.getLogger(ct.LOGGER_NAME)
    
    # シンプルなChainを実行
    result = state.simple_chain.invoke({
        "input": chat_message, 
        "chat_history": state.chat_history
    })
    # 会話履歴への追加
    state.chat_history.extend([HumanMessage(content=chat_message), AIMessage(content=result["answer"])])
    response = result["answer"]

    return response


def adjust_string(s):
    """
    Windows環境でRAGが正常動作するよう調整
    
    Args:
        s: 調整を行う文字列
    
    Returns:
        調整を行った文字列
    """
    # 調整対象は文字列のみ
    if type(s) is not str:
        return s

    # OSがWindowsの場合、Unicode正規化と、cp932（Windows用の文字コード）で表現できない文字を除去
    if sys.platform.startswith("win"):
        s = unicodedata.normalize('NFC', s)
        s = s.encode("cp932", "ignore").decode("cp932")
        return s
    
    # OSがWindows以外の場合はそのまま返す
    return s

    return s