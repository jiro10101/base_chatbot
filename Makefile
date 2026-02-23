# ══════════════════════════════════════════════════════════
# 試験実施コマンド ジェネレーター - テスト実行 Makefile
# 使い方:
#   make test          # 全テスト実行
#   make test-unit     # ユニットテストのみ（高速・ブラウザ不要）
#   make test-ui       # Streamlit UI テストのみ
#   make test-cov      # カバレッジ付きで全テスト実行
#   make install-test  # テスト用パッケージをインストール
# ══════════════════════════════════════════════════════════

.PHONY: test test-unit test-ui test-cov install-test clean-cache

# ── テスト実行 ──────────────────────────────────────────
test: test-unit test-ui
	@echo ""
	@echo "✅ 全テスト完了"

test-unit:
	@echo "=== ユニットテスト (utils.py) ==="
	pytest tests/test_utils.py -v --tb=short

test-ui:
	@echo "=== UI テスト (Streamlit AppTest) ==="
	pytest tests/test_app.py -v --tb=short

# カバレッジレポートも出力（htmlcov/ に HTML 生成）
test-cov:
	@echo "=== カバレッジ付きテスト ==="
	pytest tests/ -v --tb=short --cov=. --cov-report=term-missing --cov-report=html
	@echo "📊 HTML レポート: htmlcov/index.html"

# ── 環境セットアップ ────────────────────────────────────
install-test:
	@echo "=== テスト用パッケージをインストール ==="
	pip install pytest pytest-mock pytest-cov
	@echo "✅ インストール完了"

# ── キャッシュ削除 ──────────────────────────────────────
clean-cache:
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete 2>/dev/null; true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null; true
	@echo "🧹 キャッシュを削除しました"
