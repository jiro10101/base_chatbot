# CLAUDE.md — 試験実施コマンド ジェネレーター

## プロジェクト概要

Streamlit + LangChain + OpenAI を使用した、fio 試験スクリプト実行コマンドを自動生成する AI チャットボットアプリケーション。ユーザーが入力したパラメータを元に正しいコマンド文字列を生成し、そのままサーバー上で `screen` を使って実行する機能を持つ。

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

---

## 主要な設定値（constants.py）

| 定数 | 値 | 説明 |
|---|---|---|
| `MODEL` | `gpt-4o-mini` | 使用する OpenAI モデル |
| `TEMPERATURE` | `0.5` | LLM の温度パラメータ |
| `MAX_ALLOWED_TOKENS` | `2000` | 会話履歴の最大トークン数 |
| `ENCODING_KIND` | `cl100k_base` | tiktoken のエンコーディング種別 |
| `EXTERNAL_APP_URL` | `http://100.64.1.47:8503` | 外部アプリの URL |
| `TESTSCRIPT_TRIGGER_KEYWORD` | `/home/jiro/fioスクリプト/Testtoolsqript.sh` | コマンド検出キーワード |

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

# 環境変数の設定
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env

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
3. 正しい形式なら確認メッセージを表示、不正なら LLM に問い合わせてコマンド候補を生成
4. 有効なコマンドがある場合、サイドバーに「Screen 実行」ボタンを表示

### Screen 実行（utils.py）
- `execute_script_with_screen()` が `screen -dmS` コマンドをバックグラウンド実行
- セッション名は `{FWVer}_{testscriptファイル名}_{Model}_{Environment}` で自動生成
- 実行結果は `st.session_state` に保存し、`st.rerun()` で再レンダリング

### テスト結果の読み込み（utils.py）
- `/home/jiro/base_chatbot/results/` 内の JSON ファイルを読み込む
- ファイル名のフォーマット：`YYYYMMDD_HHMMSS_テスト種別_FW{ver}_{model}_{env}.json`
- fio の JSON 出力形式（`jobs[0]` に `read` / `write` の `iops`, `bw` が入る）

### トークン管理
- `st.session_state.total_tokens` で累計トークン数を管理
- 上限（2000）を超えた場合、`delete_old_conversation_log()` が古い会話から順に削除
- `st.session_state.chat_history`（LangChain の `HumanMessage` / `AIMessage`）と `st.session_state.messages`（表示用辞書リスト）の2系統を並行管理している点に注意

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

---

## 開発上の注意点

- `components.py` の `display_external_app_launch_option()` では `st.sidebar` 内に重複して `## Screen実行` セクションが描画される実装上のバグあり（`st.markdown("## 📺 Screen実行")` と `st.info(...)` が2回連続している）
- `utils.py` の `adjust_string()` は Windows 向けの文字コード処理だが、本番環境は Linux のため実質使用されない
- `check_testscript_response()` は定義されているが `main.py` からは直接呼ばれていない（`validate_command_format()` が代わりに使われている）
- ログは `./logs/application.log` に日次ローテーションで出力される
