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
