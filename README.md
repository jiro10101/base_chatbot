# 試験実施コマンド ジェネレーター

このプロジェクトは、Streamlit、LangChain、OpenAIを使用したスクリプト名生成AIチャットボットアプリケーションです。

## 概要

ユーザーが指定したパラメータ（FWVer、Testscript、TestingEnvironment、Model）に基づいて、指定されたフォーマットに従ったスクリプト名を自動生成するAIアシスタントです。パラメータが不足している場合は、複数の組み合わせ例を提示してユーザーをサポートします。

## セットアップ

### 1. Python環境の準備

Python 3.8以上が必要です。仮想環境の使用を推奨します。

```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
# Linux/Mac
source venv/bin/activate
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

#### Linux向けの推奨要件

Linux環境では専用のrequirementsファイルの使用を推奨します：

```bash
# Linux向け（推奨）
pip install -r requirements_linux.txt

# 汎用版
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env`ファイルを作成し、OpenAI APIキーを設定してください：

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. アプリケーションの実行

```bash
# 仮想環境を有効化
source venv/bin/activate

# Streamlitアプリを起動
streamlit run main.py
```

## 主な機能

- **スクリプト名の自動生成**: 指定されたパラメータから標準フォーマットのスクリプト名を生成
- **パラメータの入力サポート**: 
  - 必須パラメータ: FWVer、Testscript、TestingEnvironment、Model
  - パラメータ不足時は複数の組み合わせ例を提示
- **シンプルなチャットインターフェース**: Streamlitベースの使いやすいUI
- **会話履歴管理**: トークン数（上限2000）を管理して効率的な会話を維持

## 使用例

### 全パラメータ指定時
```
ユーザー: FWVer: 1.00, Model: ModelA, Testscript: /home/jiro/fioスクリプト/rand_read_simple.sh, TestingEnvironment: 100.67.161.104
AI: /home/jiro/fioスクリプト/Testtoolsqript.sh 1.00 /home/jiro/fioスクリプト/rand_read_simple.sh ModelA 100.67.161.104
```

### パラメータ不足時
```
ユーザー: FWVer: 1.20, Model: ModelB
AI: 以下を指定してください。
1. Testscript [試験スクリプト名]: 例 /home/jiro/fioスクリプト/rand_read_simple.sh, /home/jiro/fioスクリプト/rand_write_simple.sh
2. TestingEnvironment [試験環境]: 例 100.67.161.104, 192.168.20.20

[複数の組み合わせ例を3つ程度提示]
```

## 社内公開設定

アプリケーションはデフォルトで`localhost:8501`で起動します。
社内ネットワークからアクセスできるようにするには：

```bash
# すべてのネットワークインターフェースでリッスン
streamlit run main.py --server.address 0.0.0.0

# カスタムポートを指定
streamlit run main.py --server.address 0.0.0.0 --server.port 8502
```

**アクセスURL**: `http://<サーバーのIPアドレス>:8501`

IPアドレスの確認：
```bash
ip addr show
# または
hostname -I
```

## 開発者向け

### プロジェクト構成

```
base_chatbot/
├── main.py                  # メインアプリケーション
├── initialize.py            # 初期化処理（LLM、Chain作成）
├── utils.py                 # ユーティリティ関数
├── components.py            # UIコンポーネント
├── constants.py             # 定数定義（プロンプト、設定値）
├── requirements.txt         # Python依存パッケージ（汎用）
├── requirements_linux.txt   # Linux向け依存パッケージ
├── .env                     # 環境変数（APIキー等）
├── .gitignore              # Git除外設定
├── logs/                    # ログファイル
└── images/                  # アイコン画像
```

### 主要コンポーネント

- **LLMモデル**: OpenAI GPT-4o-mini
- **Temperature**: 0.5（適度な創造性と一貫性のバランス）
- **フレームワーク**: LangChain 1.0+
- **UI**: Streamlit 1.45+
- **会話管理**: LangChainのメッセージ履歴とトークンカウント（上限2000トークン）
- **エンコーディング**: cl100k_base

### 機能の特徴

- ✅ スクリプト名生成に特化したAIアシスタント
- ✅ パラメータベースの自動命名規則適用
- ✅ シンプルな構成（RAG機能なし）
- ✅ 最新のLangChain 1.0+対応
- ✅ トークン管理による効率的な会話履歴（上限2000トークン）

### 出力フォーマット

生成されるスクリプト名のフォーマット：
```
/home/jiro/fioスクリプト/Testtoolsqript.sh [FWVer] [Testscript] [Model] [TestingEnvironment]
```

**パラメータ例:**
- **FWVer**: `1.00`, `1.20`, `1.04`
- **Testscript**: `/home/jiro/fioスクリプト/rand_read_simple.sh`, `/home/jiro/fioスクリプト/rand_write_simple.sh`, `/home/jiro/fioスクリプト/seq_read_simple.sh`, `/home/jiro/fioスクリプト/seq_write_simple.sh`
- **TestingEnvironment**: `100.67.161.104`, `192.168.20.20`
- **Model**: `ModelA`, `ModelB`, `ModelC`

## トラブルシューティング

### インポートエラー

```bash
# Pythonキャッシュをクリア
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

### ポートが使用中

```bash
# 既存のStreamlitプロセスを停止
pkill -f "streamlit run"

# または別のポートを使用
streamlit run main.py --server.port 8502
```

### LangChainバージョンについて

このプロジェクトは`langchain 1.0`以降に対応しています。
必要なコンポーネントは`langchain-core`と`langchain-openai`を使用しています。

## 必要な環境

- **Python**: 3.8以上（推奨: 3.12）
- **OS**: Linux (Ubuntu 24.04での動作確認済み)
- **OpenAI APIキー**: 必須

## ライセンス

このプロジェクトは社内利用を目的としています。