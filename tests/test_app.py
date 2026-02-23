"""
Streamlit アプリの UI テスト。
streamlit.testing.v1.AppTest を使用することで、
ブラウザを起動せずにアプリの動作を検証できる。
"""

import pytest
from unittest.mock import patch, MagicMock


def make_mock_llm():
    """テスト用の ChatOpenAI モックを生成する"""
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="テスト用AIレスポンス")
    return llm


# ══════════════════════════════════════════════════════════════
# アプリ起動テスト
# ══════════════════════════════════════════════════════════════
class TestAppStartup:
    """アプリが正常に起動するかを検証する"""

    def test_app_starts_without_exception(self):
        """
        アプリが例外なく起動できる。
        OpenAI API 呼び出しはモックで代替する。
        """
        from streamlit.testing.v1 import AppTest

        with patch("langchain_openai.ChatOpenAI", return_value=make_mock_llm()), \
             patch("os.getenv", side_effect=lambda k, d=None: "test_key" if k == "OPENAI_API_KEY" else d):
            at = AppTest.from_file("../main.py", default_timeout=30)
            at.run()

        assert not at.exception, f"起動時に例外発生: {at.exception}"

    def test_chat_input_exists(self):
        """チャット入力欄が画面に表示されている"""
        from streamlit.testing.v1 import AppTest

        with patch("langchain_openai.ChatOpenAI", return_value=make_mock_llm()), \
             patch("os.getenv", side_effect=lambda k, d=None: "test_key" if k == "OPENAI_API_KEY" else d):
            at = AppTest.from_file("../main.py", default_timeout=30)
            at.run()

        assert len(at.chat_input) > 0, "chat_input が見つからない"


# ══════════════════════════════════════════════════════════════
# チャット送信テスト
# ══════════════════════════════════════════════════════════════
class TestChatInteraction:
    """ユーザーがメッセージを送信したときの動作を検証する"""

    def _run_app_with_message(self, message: str):
        """アプリを起動してメッセージを送信するヘルパー"""
        from streamlit.testing.v1 import AppTest

        # LLM チェーンが "AIの回答です" を返すようにモック
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "AIの回答です"

        with patch("langchain_openai.ChatOpenAI", return_value=make_mock_llm()), \
             patch("utils.create_simple_chain", return_value=mock_chain), \
             patch("os.getenv", side_effect=lambda k, d=None: "test_key" if k == "OPENAI_API_KEY" else d):
            at = AppTest.from_file("../main.py", default_timeout=30)
            at.run()
            at.chat_input[0].set_value(message).run()

        return at

    def test_valid_command_accepted(self):
        """
        正規フォーマットのコマンドを送信すると、
        例外なくレスポンスが返る。
        """
        cmd = (
            "/home/jiro/fioスクリプト/Testtoolsqript.sh "
            "1.00 "
            "/home/jiro/fioスクリプト/rand_read_simple.sh "
            "ModelA "
            "100.67.161.104"
        )
        at = self._run_app_with_message(cmd)
        assert not at.exception, f"例外発生: {at.exception}"

    def test_plain_text_message_accepted(self):
        """
        パラメータが不足したメッセージでも例外なく処理される
        （LLM にコマンド候補の生成を依頼するフローに入る）。
        """
        at = self._run_app_with_message("試験したいです")
        assert not at.exception, f"例外発生: {at.exception}"

    def test_valid_command_shows_confirmation(self):
        """
        正規コマンドを送信すると「コマンドの形式が正しいです」が
        チャット上に表示される。
        """
        cmd = (
            "/home/jiro/fioスクリプト/Testtoolsqript.sh "
            "1.00 "
            "/home/jiro/fioスクリプト/rand_read_simple.sh "
            "ModelA "
            "100.67.161.104"
        )
        at = self._run_app_with_message(cmd)
        messages = [m.markdown for m in at.chat_message]
        assert any("コマンドの形式が正しいです" in str(m) for m in messages), \
            "確認メッセージが表示されていない"


# ══════════════════════════════════════════════════════════════
# コマンド入力時の session_state 管理テスト
# ── main.py のコマンド検証→exec_result リセットロジックを検証する
# ══════════════════════════════════════════════════════════════
class TestCommandStateManagement:
    """コマンド入力時の current_command・exec_result 管理を検証する"""

    BASE = "/home/jiro/fioスクリプト"
    VALID_CMD = (
        f"{BASE}/Testtoolsqript.sh "
        f"1.00 "
        f"{BASE}/rand_read_simple.sh "
        f"ModelA "
        f"100.67.161.104"
    )

    def test_valid_command_sets_current_command(self):
        """正規コマンドを入力すると current_command が session_state にセットされる"""
        from streamlit.testing.v1 import AppTest
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "AIの回答です"

        with patch("langchain_openai.ChatOpenAI", return_value=make_mock_llm()), \
             patch("utils.create_simple_chain", return_value=mock_chain), \
             patch("os.getenv", side_effect=lambda k, d=None: "test_key" if k == "OPENAI_API_KEY" else d):
            at = AppTest.from_file("../main.py", default_timeout=30)
            at.run()
            at.chat_input[0].set_value(self.VALID_CMD).run()

        assert at.session_state.current_command is not None
        assert "Testtoolsqript.sh" in at.session_state.current_command

    def test_valid_command_resets_exec_result(self):
        """正規コマンドを入力するたびに exec_result が None にリセットされる（再試験可能）"""
        from streamlit.testing.v1 import AppTest
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "AIの回答です"

        with patch("langchain_openai.ChatOpenAI", return_value=make_mock_llm()), \
             patch("utils.create_simple_chain", return_value=mock_chain), \
             patch("os.getenv", side_effect=lambda k, d=None: "test_key" if k == "OPENAI_API_KEY" else d):
            at = AppTest.from_file("../main.py", default_timeout=30)
            at.run()
            at.chat_input[0].set_value(self.VALID_CMD).run()
            # Screen実行済みを模擬
            at.session_state.exec_result = {
                "success": True, "message": "成功",
                "screen_name": "test_session", "command": self.VALID_CMD,
            }
            # 同じコマンドを再入力 → exec_result がリセットされるはず
            at.chat_input[0].set_value(self.VALID_CMD).run()

        assert at.session_state.exec_result is None

    def test_different_command_also_resets_exec_result(self):
        """異なる正規コマンドを入力した場合も exec_result がリセットされる"""
        from streamlit.testing.v1 import AppTest
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "AIの回答です"
        second_cmd = (
            f"{self.BASE}/Testtoolsqript.sh "
            f"2.00 "
            f"{self.BASE}/seq_write_simple.sh "
            f"ModelB "
            f"192.168.20.20"
        )

        with patch("langchain_openai.ChatOpenAI", return_value=make_mock_llm()), \
             patch("utils.create_simple_chain", return_value=mock_chain), \
             patch("os.getenv", side_effect=lambda k, d=None: "test_key" if k == "OPENAI_API_KEY" else d):
            at = AppTest.from_file("../main.py", default_timeout=30)
            at.run()
            at.chat_input[0].set_value(self.VALID_CMD).run()
            at.session_state.exec_result = {
                "success": True, "message": "成功",
                "screen_name": "test_session", "command": self.VALID_CMD,
            }
            at.chat_input[0].set_value(second_cmd).run()

        assert at.session_state.exec_result is None


# ══════════════════════════════════════════════════════════════
# Screen実行ボタンの表示条件テスト
# ── components.py のサイドバーボタン表示ロジックを検証する
# ══════════════════════════════════════════════════════════════
class TestScreenButtonVisibility:
    """exec_result の状態に応じた Screen実行ボタンの表示・非表示を検証する"""

    BASE = "/home/jiro/fioスクリプト"
    VALID_CMD = (
        f"{BASE}/Testtoolsqript.sh "
        f"1.00 "
        f"{BASE}/rand_read_simple.sh "
        f"ModelA "
        f"100.67.161.104"
    )

    def _run_app_with_exec_result(self, exec_result):
        """コマンド設定後、指定した exec_result でサイドバーを再描画するヘルパー"""
        from streamlit.testing.v1 import AppTest
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "AIの回答です"

        with patch("langchain_openai.ChatOpenAI", return_value=make_mock_llm()), \
             patch("utils.create_simple_chain", return_value=mock_chain), \
             patch("os.getenv", side_effect=lambda k, d=None: "test_key" if k == "OPENAI_API_KEY" else d):
            at = AppTest.from_file("../main.py", default_timeout=30)
            at.run()
            at.chat_input[0].set_value(self.VALID_CMD).run()
            if exec_result is not None:
                at.session_state.exec_result = exec_result
                at.run()
        return at

    def test_screen_button_visible_when_not_executed(self):
        """exec_result が None（未実行）のとき Screen実行ボタンがサイドバーに表示される"""
        at = self._run_app_with_exec_result(None)
        labels = [b.label for b in at.sidebar.button]
        assert any("Screen実行" in label for label in labels)

    def test_screen_button_hidden_after_successful_execution(self):
        """Screen実行成功後は Screen実行ボタンがサイドバーから消える"""
        at = self._run_app_with_exec_result({
            "success": True, "message": "成功しました",
            "screen_name": "test_session", "command": self.VALID_CMD,
        })
        labels = [b.label for b in at.sidebar.button]
        assert not any("Screen実行" in label for label in labels)

    def test_screen_button_visible_after_failed_execution(self):
        """Screen実行失敗後は再試行のため Screen実行ボタンが表示されたまま"""
        at = self._run_app_with_exec_result({
            "success": False, "message": "実行に失敗しました",
            "screen_name": None, "command": self.VALID_CMD,
        })
        labels = [b.label for b in at.sidebar.button]
        assert any("Screen実行" in label for label in labels)
