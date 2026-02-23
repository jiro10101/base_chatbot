# CLAUDE.md — 試験実施コマンド ジェネレーター

## 目的

`Testtoolsqript.sh` の使い方を知らないユーザーでも、チャットボットと会話しながら試験を実施・管理できるようにする。

## 成功基準

- `Testtoolsqript.sh` の使い方を知らなくても試験を実行できる
- 試験の実施状況（実行中・完了・失敗）がチャット上で把握できる
- 過去の試験実施ログを確認できる
- 試験が失敗した場合、ユーザーがエラー内容を理解できる形でフィードバックされる

---

## プロジェクト概要

Streamlit + LangChain + OpenAI を使用した、fio 試験スクリプト実行コマンドを自動生成する AI チャットボットアプリケーション。以下の4つの機能で成功基準を満たす。

1. **コマンド自動生成**（成功基準①）: パラメータを会話形式で収集し、`Testtoolsqript.sh` の正しいコマンドを生成する
2. **実施状況の可視化**（成功基準②）: `screen` でバックグラウンド実行し、サイドバーで成功・失敗・セッション一覧をリアルタイムに表示する
3. **過去ログの確認**（成功基準③）: サイドバーの「テスト結果」タブで fio の JSON 結果ファイルを読み込み、IOPS・帯域幅を一覧表示する
4. **エラー内容のフィードバック**（成功基準④）: コマンド検証エラー・Screen 実行失敗・例外発生時に、原因をユーザーが理解できるメッセージで表示する

---

## ファイル構成と役割

| ファイル | 役割 |
|---|---|
| `main.py` | Streamlit アプリのエントリーポイント。画面描画・チャット送受信・エラーハンドリングを管理 |
| `initialize.py` | セッション初期化・ロガー設定・LLM と Chain の生成 |
| `utils.py` | LLM Chain 実行・コマンド検証・Screen 実行・セッション一覧取得・テスト結果読み込み |
| `components.py` | Streamlit UI コンポーネント（タイトル・会話ログ・サイドバー表示） |
| `constants.py` | 定数管理（プロンプト・モデル設定・エラーメッセージ・スタイル） |
| `requirements.txt` | Python 依存パッケージ（汎用） |
| `requirements_linux.txt` | Linux 向け依存パッケージ（推奨） |
| `.env` | 環境変数（`OPENAI_API_KEY` を記載。Git 管理外） |
| `images/` | UI アイコン画像 |
| `logs/` | アプリログ（日次ローテーション） |
| `Makefile` | テスト一括実行コマンド |
| `tests/conftest.py` | pytest 共通フィクスチャ（session_state・LLM・エンコーダーのモック） |
| `tests/test_utils.py` | utils.py のユニットテスト（ブラウザ不要） |
| `tests/test_app.py` | Streamlit UI テスト（ブラウザ不要） |

---

## 主要な設定値（constants.py）

| 定数 | デフォルト値 | 説明 |
|---|---|---|
| `MODEL` | `gpt-4o-mini` | 使用する OpenAI モデル |
| `TEMPERATURE` | `0.5` | LLM の温度パラメータ |
| `MAX_ALLOWED_TOKENS` | `2000` | 会話履歴の最大トークン数 |
| `ENCODING_KIND` | `cl100k_base` | tiktoken のエンコーディング種別 |
| `EXTERNAL_APP_URL` | `http://100.64.1.47:8503` | 外部アプリの URL（環境変数 `EXTERNAL_APP_URL` で上書き可） |
| `FIO_SCRIPT_DIR` | `/home/jiro/fioスクリプト` | fio スクリプトが置かれているディレクトリ（環境変数 `FIO_SCRIPT_DIR` で上書き可） |
| `TESTSCRIPT_TRIGGER_KEYWORD` | `{FIO_SCRIPT_DIR}/Testtoolsqript.sh` | コマンド検出キーワード（`FIO_SCRIPT_DIR` から自動生成） |
| `RESULTS_DIR` | `/home/jiro/streamlitfio_test/test_check_run/results` | fio 結果 JSON の格納ディレクトリ（環境変数 `RESULTS_DIR` で上書き可） |

---

## コマンドフォーマット

生成されるコマンドのフォーマット：

```
/home/jiro/fioスクリプト/Testtoolsqript.sh [FWVer] [Testscript] [Model] [TestingEnvironment]
```

### 入力パラメータ例

| パラメータ | 例 |
|---|---|
| FWVer | `1.00`, `1.20`, `1.04` |
| Testscript | `/home/jiro/fioスクリプト/rand_read_simple.sh` など |
| Model | `ModelA`, `ModelB`, `ModelC` |
| TestingEnvironment | `100.67.161.104`, `192.168.20.20` |

---

## セットアップ手順

```bash
# 仮想環境の作成・有効化
python3 -m venv venv
source venv/bin/activate

# 依存パッケージのインストール（Linux 推奨）
pip install -r requirements_linux.txt

# 環境変数の設定（パスはPC環境に合わせて変更する）
cat <<EOF > .env
OPENAI_API_KEY=your_openai_api_key_here
FIO_SCRIPT_DIR=/home/jiro/fioスクリプト
RESULTS_DIR=/home/jiro/streamlitfio_test/test_check_run/results
EXTERNAL_APP_URL=http://100.64.1.47:8503
EOF

# アプリの起動
streamlit run main.py

# 社内公開する場合
streamlit run main.py --server.address 0.0.0.0
```

---

## アーキテクチャのポイント

### LLM Chain の構造
- `initialize.py` の `initialize_llm_chain()` でセッション開始時に Chain を生成
- `utils.py` の `create_simple_chain()` が LangChain の `ChatPromptTemplate` + `ChatOpenAI` + `StrOutputParser` を組み合わせたチェーンを返す
- RAG は使用していない（シンプルな会話 Chain のみ）

### コマンド処理フロー（main.py）
1. ユーザー入力を受信
2. `utils.validate_command_format()` で正規表現によりコマンド形式を検証
3. 正しい形式なら確認メッセージを表示、不正なら LLM に問い合わせてコマンド候補を生成（**成功基準①**: ツールを知らなくても使える）
4. 有効なコマンドがある場合、サイドバーに「Screen 実行」ボタンを表示
5. 各処理で例外が発生した場合、原因を含むエラーメッセージをチャット上に表示（**成功基準④**: エラー内容をユーザーに伝える）

### Screen 実行（utils.py）
- `execute_script_with_screen()` が `screen -dmS` コマンドをバックグラウンド実行
- セッション名は `{FWVer}_{testscriptファイル名}_{Model}_{Environment}` で自動生成
- 実行結果（成功・失敗・セッション名・接続コマンド）は `st.session_state` に保存し、サイドバーにリアルタイム表示（**成功基準②**: 実施状況の可視化）
- 実行失敗時は `stderr` の内容をそのままエラーメッセージとして表示（**成功基準④**: エラー内容のフィードバック）

### テスト結果の読み込み（utils.py）
- サイドバーの「テスト結果」タブから過去の fio 試験結果を確認できる（**成功基準③**: 過去ログ確認）
- `RESULTS_DIR`（デフォルト: `/home/jiro/streamlitfio_test/test_check_run/results/`）内の JSON ファイルを新しい順に最大5件表示
- ファイル名のフォーマット：`YYYYMMDD_HHMMSS_テスト種別_FW{ver}_{model}_{env}.json`
- fio の JSON 出力形式（`jobs[0]` に `read` / `write` の `iops`, `bw` が入る）

### トークン管理
- `st.session_state.total_tokens` で累計トークン数を管理
- 上限（2000）を超えた場合、`delete_old_conversation_log()` が古い会話から順に削除
- `st.session_state.chat_history`（LangChain の `HumanMessage` / `AIMessage`）と `st.session_state.messages`（表示用辞書リスト）の2系統を並行管理している点に注意

---

## テスト

### テスト構成

ブラウザを起動せずにアプリのロジックと UI を自動検証できる。外部依存（OpenAI・subprocess・Streamlit session_state）はすべてモック化している。

| ファイル | 対象 | テスト数 |
|---|---|---|
| `tests/test_utils.py` | `utils.py` のロジック全般 | 17ケース |
| `tests/test_app.py` | Streamlit UI の起動・チャット送信動作・state管理・ボタン表示条件 | 10ケース |

### テスト実行コマンド

```bash
# 初回のみ: テスト用パッケージをインストール
make install-test

# ユニットテストのみ（高速・推奨）
make test-unit

# UI テストのみ
make test-ui

# 全テスト実行
make test

# カバレッジ付き（htmlcov/index.html にレポート生成）
make test-cov
```

### テスト対象の関数と確認内容

| テストクラス | 対象 | 主な確認内容 |
|---|---|---|
| `TestValidateCommandFormat` | `validate_command_format()` | 正規コマンドの判定・パラメータ抽出・不正コマンドの拒否 |
| `TestGetLatestTestResults` | `get_latest_test_results()` | JSON 読み込み・降順ソート・壊れたファイルのスキップ |
| `TestExecuteScriptWithScreen` | `execute_script_with_screen()` | screen 実行の成功・失敗・セッション名生成・例外処理 |
| `TestExecuteAgentOrChain` | `execute_agent_or_chain()` | LLM Chain 呼び出し・chat_history の更新 |
| `TestDeleteOldConversationLog` | `delete_old_conversation_log()` | トークン上限超過時の古い履歴削除 |
| `TestCommandStateManagement` | `main.py` コマンド検証ロジック | コマンド入力のたびに exec_result がリセットされる（同一・別コマンド両方） |
| `TestScreenButtonVisibility` | `components.py` サイドバー描画 | 未実行・成功後・失敗後それぞれのボタン表示・非表示 |

### テスト追加の方針

- `utils.py` に関数を追加したら `tests/test_utils.py` に対応するテストクラスを追加する
- 外部 API・ファイルシステム・subprocess は必ず `unittest.mock.patch` でモックする
- `conftest.py` のフィクスチャを共通化して、テスト間の重複を減らす

---

## よくあるトラブルと対処

### ポートが使用中
```bash
pkill -f "streamlit run"
streamlit run main.py --server.port 8502
```

### インポートエラー / キャッシュ問題
```bash
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

### Screen セッションの確認・接続
```bash
screen -ls                      # セッション一覧
screen -r <セッション名>         # セッションへ接続
# Ctrl+A → D でセッションから離脱
```

### 試験が失敗した場合（成功基準④）
- サイドバーの「Screen実行」タブに ❌ マークとともに `stderr` のエラー内容が表示される
- `./logs/application.log` にも詳細なエラーログが記録されているため、管理者への問い合わせ時に参照する

---

## 開発上の注意点

- `utils.py` の `adjust_string()` は Windows 向けの文字コード処理だが、本番環境は Linux のため実質使用されない
- `check_testscript_response()` は定義されているが `main.py` からは直接呼ばれていない（`validate_command_format()` が代わりに使われている）
- サイドバーの描画は `components.py` の `display_sidebar()` が担当しており、Tab1（Screen実行）・Tab2（テスト結果）の2タブ構成になっている
- ログは `./logs/application.log` に日次ローテーションで出力される
