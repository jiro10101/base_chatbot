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
import webbrowser
import urllib.parse
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


def create_simple_chain():
    """
    RAGを使用しない、シンプルな会話Chainを作成

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


def check_testscript_response(response):
    """
    LLMの回答がTestscriptを含むかチェック
    
    Args:
        response: LLMからの回答
    
    Returns:
        Testscriptを含む場合はTrue、それ以外はFalse
    """
    return ct.TESTSCRIPT_TRIGGER_KEYWORD in response


def create_external_app_url(script_name):
    """
    外部アプリのURLを生成（スクリプト名をパラメータとして含む）
    
    Args:
        script_name: 送信するスクリプト名
    
    Returns:
        パラメータ付きURL
    """
    encoded_script = urllib.parse.quote(script_name)
    return f"{ct.EXTERNAL_APP_URL}?script={encoded_script}"


def validate_command_format(command):
    """
    コマンドのフォーマットを検証
    
    Args:
        command: 検証するコマンド文字列
    
    Returns:
        dict: 検証結果（valid: bool, message: str, params: dict or None）
    """
    import re
    
    logger = logging.getLogger(ct.LOGGER_NAME)
    
    # 期待フォーマット: /home/jiro/fioスクリプト/Testtoolsqript.sh [FWVer] [Testscript] [Model] [TestingEnvironment]
    pattern = r'/home/jiro/fioスクリプト/Testtoolsqript\.sh\s+(\S+)\s+(/home/jiro/fioスクリプト/\S+\.sh)\s+(\S+)\s+([\d.]+)'
    
    match = re.search(pattern, command)
    
    if match:
        params = {
            "fw_ver": match.group(1),
            "testscript": match.group(2),
            "model": match.group(3),
            "environment": match.group(4)
        }
        
        logger.info(f"コマンド検証成功: {params}")
        
        return {
            "valid": True,
            "message": "コマンドフォーマットが正しいです",
            "params": params,
            "command": command.strip()
        }
    else:
        logger.warning(f"コマンド検証失敗: {command}")
        
        return {
            "valid": False,
            "message": "コマンドフォーマットが正しくありません",
            "params": None,
            "command": command.strip()
        }


def execute_script_with_screen(script_command):
    """
    screenコマンドを使用してスクリプトを実行
    
    Args:
        script_command: 実行するスクリプトコマンド
                       例: "/home/jiro/fioスクリプト/Testtoolsqript.sh 1.00 /home/jiro/fioスクリプト/rand_read_simple.sh ModelA 100.67.161.104"
    
    Returns:
        dict: 実行結果（success: bool, message: str, screen_name: str or None, command: str）
    """
    import subprocess
    
    logger = logging.getLogger(ct.LOGGER_NAME)
    
    logger.info(f"========== Screen実行開始 ==========")
    logger.info(f"入力コマンド: {script_command}")
    
    # まずコマンドフォーマットを検証
    validation = validate_command_format(script_command)
    
    if not validation["valid"]:
        logger.error(f"コマンド検証失敗: {validation['message']}")
        return {
            "success": False,
            "message": f"コマンドフォーマットが不正です: {validation['message']}",
            "screen_name": None,
            "command": script_command
        }
    
    try:
        params = validation["params"]
        logger.info(f"解析されたパラメータ: FWVer={params['fw_ver']}, Model={params['model']}, Testscript={params['testscript']}, Environment={params['environment']}")
        
        # screen セッション名を生成（パスを除いたファイル名のみ使用）
        testscript_name = params["testscript"].split("/")[-1]
        screen_name = f"{params['fw_ver']}_{testscript_name}_{params['model']}_{params['environment']}"
        
        # screenコマンドを構築
        screen_command = f'screen -dmS "{screen_name}" {script_command}'
        
        logger.info(f"生成されたScreenセッション名: {screen_name}")
        logger.info(f"実行するscreenコマンド: {screen_command}")
        
        # screenコマンドを実行
        result = subprocess.run(
            screen_command,
            shell=True,
            executable='/bin/bash',
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Screen実行成功")
            logger.info(f"セッション名: {screen_name}")
            logger.info(f"確認コマンド: screen -ls | grep {screen_name}")
            logger.info(f"接続コマンド: screen -r {screen_name}")
            logger.info(f"========== Screen実行完了 ==========")
            
            return {
                "success": True,
                "message": f"screen セッション '{screen_name}' で実行開始しました",
                "screen_name": screen_name,
                "command": screen_command
            }
        else:
            logger.error(f"❌ Screen実行エラー")
            logger.error(f"リターンコード: {result.returncode}")
            logger.error(f"標準エラー出力: {result.stderr}")
            logger.info(f"========== Screen実行失敗 ==========")
            
            return {
                "success": False,
                "message": f"実行に失敗しました: {result.stderr}",
                "screen_name": None,
                "command": screen_command
            }
            
    except Exception as e:
        logger.error(f"❌ Screen実行中に例外発生: {e}", exc_info=True)
        logger.info(f"========== Screen実行失敗（例外） ==========")
        
        return {
            "success": False,
            "message": f"実行に失敗しました: {str(e)}",
            "screen_name": None,
            "command": script_command
        }


def get_screen_sessions():
    """
    現在のscreenセッション一覧を取得
    
    Returns:
        dict: セッション情報（success: bool, sessions: list, message: str）
    """
    import subprocess
    
    try:
        result = subprocess.run(
            ["screen", "-ls"],
            capture_output=True,
            text=True
        )
        
        sessions = []
        for line in result.stdout.split('\n'):
            # セッション情報の行を抽出（例: 12345.session_name）
            if '\t' in line and '.' in line:
                sessions.append(line.strip())
        
        return {
            "success": True,
            "sessions": sessions,
            "message": f"{len(sessions)}個のセッションが見つかりました"
        }
        
    except Exception as e:
        return {
            "success": False,
            "sessions": [],
            "message": f"セッション取得に失敗しました: {str(e)}"
        }


def get_latest_test_results(limit=5):
    """
    最新のテスト結果ファイルを取得
    
    Args:
        limit: 取得する結果ファイル数（デフォルト: 5）
    
    Returns:
        dict: 結果情報（success: bool, results: list, message: str）
    """
    import os
    import json
    import logging
    from datetime import datetime
    import constants as ct
    
    logger = logging.getLogger(ct.LOGGER_NAME)
    results_dir = "/home/jiro/base_chatbot/results"
    
    try:
        if not os.path.exists(results_dir):
            return {
                "success": False,
                "results": [],
                "message": "結果ディレクトリが存在しません"
            }
        
        # JSONファイルを取得
        json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
        
        if not json_files:
            return {
                "success": True,
                "results": [],
                "message": "結果ファイルがありません"
            }
        
        # ファイル名でソート（新しい順）
        json_files.sort(reverse=True)
        
        results = []
        for filename in json_files[:limit]:
            filepath = os.path.join(results_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # ファイル名から情報を抽出
                # 例: 20251130_110020_randread_FW1.00_ModelA_100.67.161.104.json
                parts = filename.replace('.json', '').split('_')
                
                # 基本情報
                result_info = {
                    "filename": filename,
                    "filepath": filepath,
                    "timestamp": parts[0] + "_" + parts[1] if len(parts) > 1 else "不明",
                    "test_type": parts[2] if len(parts) > 2 else "不明",
                    "fw_ver": parts[3] if len(parts) > 3 else "不明",
                    "model": parts[4] if len(parts) > 4 else "不明",
                    "environment": parts[5] if len(parts) > 5 else "不明"
                }
                
                # fio結果から性能情報を抽出
                if "jobs" in data and len(data["jobs"]) > 0:
                    job = data["jobs"][0]
                    
                    # Read性能
                    if "read" in job and "iops" in job["read"]:
                        result_info["read_iops"] = round(job["read"]["iops"], 2)
                        result_info["read_bw_mb"] = round(job["read"]["bw"] / 1024, 2)
                    
                    # Write性能
                    if "write" in job and "iops" in job["write"]:
                        result_info["write_iops"] = round(job["write"]["iops"], 2)
                        result_info["write_bw_mb"] = round(job["write"]["bw"] / 1024, 2)
                    
                    # ジョブオプション
                    if "job options" in job:
                        opts = job["job options"]
                        result_info["rw_type"] = opts.get("rw", "不明")
                        result_info["bs"] = opts.get("bs", "不明")
                        result_info["iodepth"] = opts.get("iodepth", "不明")
                
                results.append(result_info)
                
            except Exception as e:
                logger.warning(f"結果ファイル読み込みエラー ({filename}): {e}")
                continue
        
        return {
            "success": True,
            "results": results,
            "message": f"{len(results)}件の結果を取得しました"
        }
        
    except Exception as e:
        logger.error(f"結果取得中にエラー: {e}", exc_info=True)
        return {
            "success": False,
            "results": [],
            "message": f"結果取得に失敗しました: {str(e)}"
        }