"""
utils.py のユニットテスト。
Streamlit・OpenAI・subprocess など外部依存はすべてモック化し、
ブラウザ不要・ネット不要でローカル実行できる。
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage


# ══════════════════════════════════════════════════════════════
# validate_command_format のテスト
# ── コマンド形式の正規表現バリデーションを検証する
# ══════════════════════════════════════════════════════════════
class TestValidateCommandFormat:
    """validate_command_format() の正常・異常系テスト"""

    BASE = "/home/jiro/fioスクリプト"
    VALID_CMD = (
        f"{BASE}/Testtoolsqript.sh "
        f"1.00 "
        f"{BASE}/rand_read_simple.sh "
        f"ModelA "
        f"100.67.161.104"
    )

    def test_valid_command_returns_true(self):
        """正規フォーマットのコマンドは valid=True を返す"""
        import utils
        result = utils.validate_command_format(self.VALID_CMD)
        assert result["valid"] is True

    def test_valid_command_params(self):
        """正規フォーマットのパラメータが正しく抽出される"""
        import utils
        result = utils.validate_command_format(self.VALID_CMD)
        params = result["params"]
        assert params["fw_ver"] == "1.00"
        assert params["model"] == "ModelA"
        assert params["environment"] == "100.67.161.104"
        assert params["testscript"].endswith("rand_read_simple.sh")

    def test_invalid_plain_text(self):
        """平文テキストは invalid を返す"""
        import utils
        result = utils.validate_command_format("こんにちは、試験をしたいです")
        assert result["valid"] is False
        assert result["params"] is None

    def test_invalid_missing_environment(self):
        """環境IP が欠けている場合は invalid"""
        import utils
        cmd = f"{self.BASE}/Testtoolsqript.sh 1.00 {self.BASE}/rand_read_simple.sh ModelA"
        result = utils.validate_command_format(cmd)
        assert result["valid"] is False

    def test_invalid_wrong_script_name(self):
        """スクリプト名が Testtoolsqript.sh でない場合は invalid"""
        import utils
        cmd = f"{self.BASE}/WrongScript.sh 1.00 {self.BASE}/rand_read_simple.sh ModelA 100.67.161.104"
        result = utils.validate_command_format(cmd)
        assert result["valid"] is False

    def test_valid_different_fw_versions(self):
        """FWVer のバリエーション（1.20, 1.04）も正しく検証される"""
        import utils
        for fw in ["1.20", "1.04", "2.00"]:
            cmd = f"{self.BASE}/Testtoolsqript.sh {fw} {self.BASE}/seq_write_simple.sh ModelB 192.168.20.20"
            result = utils.validate_command_format(cmd)
            assert result["valid"] is True, f"FWVer={fw} で失敗"
            assert result["params"]["fw_ver"] == fw

    def test_command_returned_in_result(self):
        """result['command'] に検出されたコマンド文字列が含まれる"""
        import utils
        result = utils.validate_command_format(self.VALID_CMD)
        assert result["command"] != ""


# ══════════════════════════════════════════════════════════════
# get_latest_test_results のテスト
# ── RESULTS_DIR の JSON ファイル読み込みと fio データ解析を検証する
# ══════════════════════════════════════════════════════════════
class TestGetLatestTestResults:
    """get_latest_test_results() の正常・異常系テスト"""

    FIO_JSON = {
        "jobs": [{
            "read":  {"iops": 1000.5, "bw": 512000},
            "write": {"iops": 0.0,    "bw": 0},
            "job options": {"rw": "randread", "bs": "4k", "iodepth": "32"}
        }]
    }

    def test_nonexistent_dir_returns_failure(self):
        """存在しないディレクトリは success=False を返す"""
        import utils, constants as ct
        with patch.object(ct, "RESULTS_DIR", "/nonexistent/path/xyz"):
            result = utils.get_latest_test_results()
        assert result["success"] is False

    def test_empty_dir_returns_empty_list(self, tmp_path):
        """JSON ファイルがないディレクトリは空リストを返す"""
        import utils, constants as ct
        with patch.object(ct, "RESULTS_DIR", str(tmp_path)):
            result = utils.get_latest_test_results()
        assert result["success"] is True
        assert result["results"] == []

    def test_reads_single_json_file(self, tmp_path):
        """1件の JSON ファイルを正しく読み込む"""
        import utils, constants as ct
        fname = "20251130_110020_randread_FW1.00_ModelA_100.67.161.104.json"
        (tmp_path / fname).write_text(json.dumps(self.FIO_JSON), encoding="utf-8")

        with patch.object(ct, "RESULTS_DIR", str(tmp_path)):
            result = utils.get_latest_test_results()

        assert result["success"] is True
        assert len(result["results"]) == 1
        r = result["results"][0]
        assert r["read_iops"] == 1000.5
        assert r["read_bw_mb"] == pytest.approx(512000 / 1024, rel=1e-3)

    def test_limit_is_respected(self, tmp_path):
        """limit=3 の場合、最大3件しか返さない"""
        import utils, constants as ct
        for i in range(6):
            fname = f"2025113{i}_110020_randread_FW1.00_ModelA_100.67.161.104.json"
            (tmp_path / fname).write_text(json.dumps(self.FIO_JSON), encoding="utf-8")

        with patch.object(ct, "RESULTS_DIR", str(tmp_path)):
            result = utils.get_latest_test_results(limit=3)

        assert len(result["results"]) == 3

    def test_newest_first_ordering(self, tmp_path):
        """新しいファイルが先頭に来る（降順ソート）"""
        import utils, constants as ct
        files = [
            "20251101_000000_randread_FW1.00_ModelA_100.67.161.104.json",
            "20251201_000000_randread_FW1.00_ModelA_100.67.161.104.json",
            "20251115_000000_randread_FW1.00_ModelA_100.67.161.104.json",
        ]
        for f in files:
            (tmp_path / f).write_text(json.dumps(self.FIO_JSON), encoding="utf-8")

        with patch.object(ct, "RESULTS_DIR", str(tmp_path)):
            result = utils.get_latest_test_results()

        # 先頭が最新（20251201）
        assert result["results"][0]["timestamp"].startswith("20251201")

    def test_malformed_json_is_skipped(self, tmp_path):
        """壊れた JSON ファイルはスキップして他のファイルを返す"""
        import utils, constants as ct
        (tmp_path / "20251130_000000_randread_FW1.00_ModelA_100.67.161.104.json").write_text(
            json.dumps(self.FIO_JSON), encoding="utf-8"
        )
        (tmp_path / "20251129_000000_randread_FW1.00_ModelA_100.67.161.104.json").write_text(
            "{ broken json }", encoding="utf-8"
        )

        with patch.object(ct, "RESULTS_DIR", str(tmp_path)):
            result = utils.get_latest_test_results()

        assert result["success"] is True
        assert len(result["results"]) == 1  # 壊れた分はスキップ


# ══════════════════════════════════════════════════════════════
# execute_script_with_screen のテスト
# ── subprocess をモックして screen 実行を検証する
# ══════════════════════════════════════════════════════════════
class TestExecuteScriptWithScreen:
    """execute_script_with_screen() の正常・異常系テスト"""

    VALID_CMD = (
        "/home/jiro/fioスクリプト/Testtoolsqript.sh "
        "1.00 "
        "/home/jiro/fioスクリプト/rand_read_simple.sh "
        "ModelA "
        "100.67.161.104"
    )

    def _make_proc(self, returncode=0, stderr=""):
        """subprocess.run の戻り値モックを生成するヘルパー"""
        m = MagicMock()
        m.returncode = returncode
        m.stderr = stderr
        return m

    def test_success(self):
        """screen 実行が成功した場合、success=True とセッション名を返す"""
        import utils
        with patch("subprocess.run", return_value=self._make_proc(0)):
            result = utils.execute_script_with_screen(self.VALID_CMD)
        assert result["success"] is True
        assert result["screen_name"] is not None

    def test_screen_name_contains_params(self):
        """セッション名に FWVer・スクリプト名・モデル・環境が含まれる"""
        import utils
        with patch("subprocess.run", return_value=self._make_proc(0)):
            result = utils.execute_script_with_screen(self.VALID_CMD)
        name = result["screen_name"]
        assert "1.00" in name
        assert "ModelA" in name
        assert "100.67.161.104" in name
        assert "rand_read_simple.sh" in name

    def test_failure_returns_stderr(self):
        """screen 実行失敗時、stderr の内容がメッセージに含まれる"""
        import utils
        with patch("subprocess.run", return_value=self._make_proc(1, "screen: command not found")):
            result = utils.execute_script_with_screen(self.VALID_CMD)
        assert result["success"] is False
        assert "screen: command not found" in result["message"]

    def test_invalid_command_rejected(self):
        """不正なコマンドは subprocess を呼び出す前に弾かれる"""
        import utils
        with patch("subprocess.run") as mock_run:
            result = utils.execute_script_with_screen("invalid command")
        assert result["success"] is False
        mock_run.assert_not_called()  # subprocess が呼ばれていないことを確認

    def test_exception_handling(self):
        """subprocess が例外を送出しても success=False を返しクラッシュしない"""
        import utils
        with patch("subprocess.run", side_effect=Exception("OS error")):
            result = utils.execute_script_with_screen(self.VALID_CMD)
        assert result["success"] is False
        assert "OS error" in result["message"]


# ══════════════════════════════════════════════════════════════
# execute_agent_or_chain のテスト
# ══════════════════════════════════════════════════════════════
class TestExecuteAgentOrChain:
    """execute_agent_or_chain() が Chain を正しく呼び出すかを検証する"""

    def test_returns_llm_response(self, session_state_with_chain):
        """LLM Chain の応答がそのまま返る"""
        import utils
        result = utils.execute_agent_or_chain("テスト入力")
        assert result == "AIの回答です"

    def test_chat_history_updated(self, session_state_with_chain):
        """実行後に chat_history に HumanMessage と AIMessage が追加される"""
        import utils
        import streamlit as st
        utils.execute_agent_or_chain("ユーザー発言")
        history = st.session_state.chat_history
        assert any(isinstance(m, HumanMessage) for m in history)
        assert any(isinstance(m, AIMessage) for m in history)


# ══════════════════════════════════════════════════════════════
# delete_old_conversation_log のテスト
# ══════════════════════════════════════════════════════════════
class TestDeleteOldConversationLog:
    """トークン超過時に古い履歴が削除されるかを検証する"""

    def test_no_deletion_within_limit(self, mock_streamlit_session_state, mock_encoder):
        """トークン数が上限以内なら履歴は削除されない"""
        import utils, streamlit as st, constants as ct
        st.session_state.enc = mock_encoder
        st.session_state.total_tokens = 0
        st.session_state.chat_history = [
            HumanMessage(content="msg1"),
            AIMessage(content="msg2"),
        ]
        utils.delete_old_conversation_log("短い応答")
        assert len(st.session_state.chat_history) == 2

    def test_deletion_when_over_limit(self, mock_streamlit_session_state, mock_encoder):
        """トークン数が上限を超えた場合、古い履歴（インデックス1）が削除される"""
        import utils, streamlit as st, constants as ct
        st.session_state.enc = mock_encoder
        # 現在のトークン数を上限ギリギリに設定
        st.session_state.total_tokens = ct.MAX_ALLOWED_TOKENS
        st.session_state.chat_history = [
            HumanMessage(content="system"),  # index 0: 削除されない
            HumanMessage(content="old_msg"),  # index 1: 削除対象
            AIMessage(content="recent"),
        ]
        # 追加の応答でトークン超過を引き起こす
        utils.delete_old_conversation_log("追加応答")
        # 最古の会話（index 1）が削除されていることを確認
        assert all(
            m.content != "old_msg"
            for m in st.session_state.chat_history
        )
