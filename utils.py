"""
このファイルは、画面表示以外の様々な関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import os
from dotenv import load_dotenv
import streamlit as st
import logging
import sys
import unicodedata
import requests
import json
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from typing import List, Optional, Dict
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


def create_simple_chain(redmine_info: Optional[str] = None):
    """
    RAGを使用しない、シンプルな会話Chainを作成

    Args:
        redmine_info: Redmineチケット情報（オプション）

    Returns:
        会話Chain
    """
    logger = logging.getLogger(ct.LOGGER_NAME)

    # Redmine情報がある場合はそれを含むプロンプトを使用
    if redmine_info:
        question_answer_template = ct.SYSTEM_PROMPT_INQUIRY.format(redmine_info=redmine_info)
    else:
        question_answer_template = ct.SYSTEM_PROMPT_NO_REDMINE
    
    question_answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", question_answer_template),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # LLMとプロンプトを組み合わせたチェーンを作成
    
    chain = question_answer_prompt | st.session_state.llm | StrOutputParser()
    
    # 入力形式を統一するためのラッパー
    def wrapped_chain(self, inputs):
        return {
            "answer": chain.invoke({
                "input": inputs["input"],
                "chat_history": inputs.get("chat_history", [])
            })
        }
    
    return type('SimpleChain', (), {'invoke': wrapped_chain})()




def delete_old_conversation_log(result):
    """
    古い会話履歴の削除

    Args:
        result: LLMからの回答
    """
    # LLMからの回答テキストのトークン数を取得
    response_tokens = len(st.session_state.enc.encode(result))
    # 過去の会話履歴の合計トークン数に加算
    st.session_state.total_tokens += response_tokens

    # トークン数が上限値を下回るまで、順に古い会話履歴を削除
    while st.session_state.total_tokens > ct.MAX_ALLOWED_TOKENS:
        # 最も古い会話履歴を削除
        removed_message = st.session_state.chat_history.pop(1)
        # 最も古い会話履歴のトークン数を取得
        removed_tokens = len(st.session_state.enc.encode(removed_message.content))
        # 過去の会話履歴の合計トークン数から、最も古い会話履歴のトークン数を引く
        st.session_state.total_tokens -= removed_tokens


def execute_agent_or_chain(chat_message):
    """
    シンプルなChainを実行

    Args:
        chat_message: ユーザーメッセージ
    
    Returns:
        LLMからの回答
    """
    logger = logging.getLogger(ct.LOGGER_NAME)
    
    
    # シンプルなChainを実行
    result = st.session_state.simple_chain.invoke({
        "input": chat_message, 
        "chat_history": st.session_state.chat_history
    })
    # 会話履歴への追加
    st.session_state.chat_history.extend([HumanMessage(content=chat_message), AIMessage(content=result["answer"])])
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


def get_redmine_issue(issue_id: str) -> Optional[Dict]:
    """
    RedmineのチケットIDから情報を取得
    
    Args:
        issue_id: RedmineのチケットID
    
    Returns:
        チケット情報の辞書、エラー時はNone
    """
    logger = logging.getLogger(ct.LOGGER_NAME)
    
    # 環境変数からRedmine設定を取得
    redmine_url = os.getenv("REDMINE_URL", ct.REDMINE_URL)
    redmine_api_key = os.getenv("REDMINE_API_KEY", ct.REDMINE_API_KEY)
    
    if not redmine_url or not redmine_api_key:
        logger.error("Redmine URLまたはAPIキーが設定されていません")
        return None
    
    try:
        # Redmine API呼び出し
        url = f"{redmine_url}/issues/{issue_id}.json"
        headers = {
            "X-Redmine-API-Key": redmine_api_key,
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        issue_data = response.json()
        
        # 必要な情報を抽出
        issue = issue_data.get("issue", {})
        
        formatted_info = {
            "id": issue.get("id"),
            "subject": issue.get("subject"),
            "description": issue.get("description", ""),
            "status": issue.get("status", {}).get("name", ""),
            "priority": issue.get("priority", {}).get("name", ""),
            "assigned_to": issue.get("assigned_to", {}).get("name", "未割り当て"),
            "created_on": issue.get("created_on", ""),
            "updated_on": issue.get("updated_on", "")
        }
        
        logger.info(f"Redmineチケット #{issue_id} の情報を取得しました")
        return formatted_info
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Redmine API呼び出しエラー: {e}")
        return None
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        return None


def format_redmine_info_for_prompt(issue_info: Dict) -> str:
    """
    Redmineチケット情報をプロンプト用にフォーマット
    
    Args:
        issue_info: チケット情報の辞書
    
    Returns:
        フォーマットされた文字列
    """
    if not issue_info:
        return "参照するRedmineチケット情報はありません。"
    
    formatted = f"""
## 参照チケット情報 (#{issue_info['id']})

**題名:** {issue_info['subject']}

**ステータス:** {issue_info['status']}
**優先度:** {issue_info['priority']}
**担当者:** {issue_info['assigned_to']}

**説明:**
{issue_info['description']}

**作成日:** {issue_info['created_on']}
**更新日:** {issue_info['updated_on']}
"""
    return formatted


def extract_redmine_issue_id(message: str) -> Optional[str]:
    """
    ユーザーメッセージからRedmineチケットIDを抽出
    
    Args:
        message: ユーザーメッセージ
    
    Returns:
        チケットID（見つからない場合はNone）
    """
    import re
    
    # Redmine番号のパターン（#12345 または 12345）
    patterns = [
        r'#(\d+)',  # #12345
        r'[Rr]edmine\s*[:#]?\s*(\d+)',  # Redmine: 12345
        r'チケット\s*[:#]?\s*(\d+)',  # チケット: 12345
        r'^\s*(\d+)\s*$'  # 12345 (数字のみ)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1)
    
    return None