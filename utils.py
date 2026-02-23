"""
画面表示以外のロジック（LLM Chain・コマンド検証・Screen実行・結果読み込み）を定義するファイル
"""

import os
import re
import json
import logging
import subprocess
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
import constants as ct


def build_error_message(message):
    """エラーメッセージに管理者問い合わせ文を付加して返す"""
    return "\n".join([message, ct.COMMON_ERROR_MESSAGE])


def create_simple_chain():
    """
    LangChain LCEL パイプラインを構築して返す。
    構成: システムプロンプト + 会話履歴 + ユーザー入力 → LLM → 文字列出力
    RAGは使用しない。
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", ct.SYSTEM_PROMPT_INQUIRY),
        MessagesPlaceholder("chat_history"),  # 過去の会話を注入するプレースホルダー
        ("human", "{input}"),
    ])
    # パイプ演算子で prompt → LLM → 文字列パーサー を直列接続（LCEL）
    return prompt | st.session_state.llm | StrOutputParser()


def delete_old_conversation_log(result):
    """
    LLM応答のトークン数を累計に加算し、上限を超えた場合は古い履歴を削除する。
    chat_history[0] はシステムメッセージなので、pop(1) から削除する。
    """
    response_tokens = len(st.session_state.enc.encode(result))
    st.session_state.total_tokens += response_tokens

    while st.session_state.total_tokens > ct.MAX_ALLOWED_TOKENS:
        # インデックス0はシステムプロンプトのため、1番目（最古の会話）から削除
        removed_message = st.session_state.chat_history.pop(1)
        removed_tokens = len(st.session_state.enc.encode(removed_message.content))
        st.session_state.total_tokens -= removed_tokens


def execute_agent_or_chain(chat_message):
    """
    LLM Chain を実行してAI応答を返す。
    実行後、ユーザー発言とAI応答の両方を chat_history に追記する。
    """
    result = st.session_state.simple_chain.invoke({
        "input": chat_message,
        "chat_history": st.session_state.chat_history
    })
    # 次回以降の会話コンテキストとして履歴に追加
    st.session_state.chat_history.extend([
        HumanMessage(content=chat_message),
        AIMessage(content=result)
    ])
    return result


def validate_command_format(command):
    """
    入力文字列が fio 試験コマンドの正規フォーマットかどうかを検証する。
    期待フォーマット:
        {FIO_SCRIPT_DIR}/Testtoolsqript.sh [FWVer] [Testscript] [Model] [Environment]
        ※ FIO_SCRIPT_DIR は環境変数で変更可能（constants.py 参照）
    戻り値: dict { valid, message, params, command }
    """
    logger = logging.getLogger(ct.LOGGER_NAME)

    # グループ1: FWVer / グループ2: テストスクリプトパス / グループ3: Model / グループ4: 環境IPアドレス
    # パスは環境変数 FIO_SCRIPT_DIR に依存するため、定数から動的に生成する
    trigger  = re.escape(ct.TESTSCRIPT_TRIGGER_KEYWORD)
    script_dir = re.escape(ct.FIO_SCRIPT_DIR)
    pattern = rf'{trigger}\s+(\S+)\s+({script_dir}/\S+\.sh)\s+(\S+)\s+([\d.]+)'
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
            "command": match.group(0).strip()
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
    screen のデタッチモード（-dmS）でスクリプトをバックグラウンド実行する。
    セッション名は {FWVer}_{スクリプトファイル名}_{Model}_{環境IP} で自動生成。
    戻り値: dict { success, message, screen_name, command }
    """
    logger = logging.getLogger(ct.LOGGER_NAME)
    logger.info(f"========== Screen実行開始 ==========")
    logger.info(f"入力コマンド: {script_command}")

    # 実行前にコマンド形式を検証
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

        # セッション名にはスクリプトのファイル名のみ使用（パス部分を除去）
        testscript_name = params["testscript"].split("/")[-1]
        screen_name = f"{params['fw_ver']}_{testscript_name}_{params['model']}_{params['environment']}"

        # -d: デタッチ状態で起動 / -m: 新規セッション強制作成 / -S: セッション名指定
        screen_command = f'screen -dmS "{screen_name}" {script_command}'
        logger.info(f"生成されたScreenセッション名: {screen_name}")
        logger.info(f"実行するscreenコマンド: {screen_command}")

        result = subprocess.run(
            screen_command,
            shell=True,
            executable='/bin/bash',
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info(f"✅ Screen実行成功 セッション名: {screen_name}")
            logger.info(f"========== Screen実行完了 ==========")
            return {
                "success": True,
                "message": f"screen セッション '{screen_name}' で実行開始しました",
                "screen_name": screen_name,
                "command": screen_command
            }
        else:
            logger.error(f"❌ Screen実行エラー: {result.stderr}")
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
    `screen -ls` の出力をパースして、アクティブなセッション一覧を返す。
    セッション行はタブ文字とドットを含む形式（例: "  12345.session_name (Detached)"）。
    戻り値: dict { success, sessions, message }
    """
    try:
        result = subprocess.run(["screen", "-ls"], capture_output=True, text=True)

        sessions = []
        for line in result.stdout.split('\n'):
            # セッション情報行はタブ始まりで "PID.セッション名" の形式
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
    RESULTS_DIR 内の JSON ファイルを新しい順に取得し、fio 結果を解析して返す。
    ファイル名フォーマット: YYYYMMDD_HHMMSS_テスト種別_FW{ver}_{model}_{env}.json
    fio JSON の jobs[0] から read/write の iops・bw を抽出する。
    戻り値: dict { success, results, message }
    """
    logger = logging.getLogger(ct.LOGGER_NAME)
    results_dir = ct.RESULTS_DIR

    try:
        if not os.path.exists(results_dir):
            return {"success": False, "results": [], "message": "結果ディレクトリが存在しません"}

        json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
        if not json_files:
            return {"success": True, "results": [], "message": "結果ファイルがありません"}

        # ファイル名が YYYYMMDD_HHMMSS... 形式のため、降順ソートで新しい順になる
        json_files.sort(reverse=True)

        results = []
        for filename in json_files[:limit]:
            filepath = os.path.join(results_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # ファイル名を "_" で分割してメタ情報を取得
                # 例: ["20251130", "110020", "randread", "FW1.00", "ModelA", "100.67.161.104"]
                parts = filename.replace('.json', '').split('_')
                result_info = {
                    "filename": filename,
                    "filepath": filepath,
                    "timestamp": parts[0] + "_" + parts[1] if len(parts) > 1 else "不明",
                    "test_type": parts[2] if len(parts) > 2 else "不明",
                    "fw_ver":    parts[3] if len(parts) > 3 else "不明",
                    "model":     parts[4] if len(parts) > 4 else "不明",
                    "environment": parts[5] if len(parts) > 5 else "不明"
                }

                # fio JSON 構造: jobs[0].read / jobs[0].write に iops・bw（KB/s）が格納される
                if "jobs" in data and len(data["jobs"]) > 0:
                    job = data["jobs"][0]

                    if "read" in job and "iops" in job["read"]:
                        result_info["read_iops"] = round(job["read"]["iops"], 2)
                        result_info["read_bw_mb"] = round(job["read"]["bw"] / 1024, 2)  # KB/s → MB/s

                    if "write" in job and "iops" in job["write"]:
                        result_info["write_iops"] = round(job["write"]["iops"], 2)
                        result_info["write_bw_mb"] = round(job["write"]["bw"] / 1024, 2)  # KB/s → MB/s

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
        return {"success": False, "results": [], "message": f"結果取得に失敗しました: {str(e)}"}
