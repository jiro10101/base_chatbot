"""
pytest 共通フィクスチャ。
Streamlit の session_state や LLM など、外部依存をまとめてモック化する。
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# プロジェクトルートを sys.path に追加（tests/ から親ディレクトリのモジュールを import できるようにする）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def mock_streamlit_session_state(monkeypatch):
    """
    Streamlit の session_state を辞書ライクなオブジェクトでモック。
    utils.py 内の st.session_state 参照をテスト環境でも動作させる。
    """
    import streamlit as st

    class FakeSessionState(dict):
        """st.session_state の属性アクセス（dot記法）と辞書アクセスの両方をサポート"""
        def __getattr__(self, key):
            try:
                return self[key]
            except KeyError:
                raise AttributeError(key)

        def __setattr__(self, key, value):
            self[key] = value

        def __delattr__(self, key):
            del self[key]

    fake_state = FakeSessionState()
    monkeypatch.setattr(st, "session_state", fake_state)
    return fake_state


@pytest.fixture
def mock_llm():
    """ChatOpenAI のモック"""
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="モックレスポンス")
    return llm


@pytest.fixture
def mock_encoder():
    """tiktoken エンコーダーのモック（トークン数を文字数で代替）"""
    encoder = MagicMock()
    encoder.encode.side_effect = lambda text: list(text)  # 文字数 = トークン数とみなす
    return encoder


@pytest.fixture
def session_state_with_chain(mock_streamlit_session_state, mock_llm, mock_encoder):
    """
    execute_agent_or_chain() が動作するのに必要な session_state をセットアップ。
    """
    import streamlit as st
    from unittest.mock import MagicMock

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = "AIの回答です"

    st.session_state.simple_chain = mock_chain
    st.session_state.chat_history = []
    st.session_state.enc = mock_encoder
    st.session_state.total_tokens = 0
    return st.session_state
