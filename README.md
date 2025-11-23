# 試験実施AIエージェント

このプロジェクトは、Taipy、LangChain、OpenAIを使用したシンプルなLinuxコマンド生成チャットボットアプリケーションです。

## 概要

ユーザーの自然言語による指示を、Linux (Ubuntu 24.04) のbashコマンドに変換するAIアシスタントです。
特に`fio`コマンドを使用したディスクI/Oベンチマーク測定を安全に実行するための制約が組み込まれています。

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

#### Linux向けの追加要件

プラットフォーム別のrequirementsファイルも利用可能です：

```bash
# Linux
pip install -r requirements_linux.txt
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

# Taipyアプリを起動
python main.py
```

## 主な機能

- **自然言語からbashコマンドへの変換**: 日本語の指示をLinuxコマンドに変換
- **fio安全実行制約**: 
  - 対象デバイス: `/dev/nvme0n1`に限定
  - 最大実行時間: 10秒以下
  - 必須パラメータの自動付与
- **シンプルなチャットインターフェース**: Taipy GUIベースの使いやすいUI
- **会話履歴管理**: トークン数を管理して効率的な会話を維持

## 使用例

```
ユーザー: SeqWriteを測定して
AI: fio --name=test --filename=/dev/nvme0n1 --direct=1 --rw=write --runtime=10 --time_based --group_reporting

ユーザー: ディスクの空き容量を見せて
AI: df -h
```

## 社内公開設定

デフォルトで社内ネットワークからアクセス可能な設定になっています：

- **アドレス**: `0.0.0.0` (すべてのネットワークインターフェースでリッスン)
- **ポート**: `8501`
- **アクセスURL**: `http://<サーバーのIPアドレス>:8501`

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
├── main.py              # メインアプリケーション（Taipy GUI）
├── initialize.py        # 初期化処理（LLM、Chain作成）
├── utils.py            # ユーティリティ関数
├── components.py       # UIコンポーネント
├── constants.py        # 定数定義（プロンプト、設定値）
├── requirements.txt    # Python依存パッケージ
├── data/              # データディレクトリ
├── logs/              # ログファイル
└── images/            # アイコン画像
```

### 主要コンポーネント

- **LLMモデル**: OpenAI GPT-4o-mini
- **フレームワーク**: LangChain (Classic) 1.0+
- **UI**: Taipy 3.0+
- **会話管理**: LangChainのメッセージ履歴とトークンカウント

### 最近の変更

- ✅ StreamlitからTaipyへUIフレームワークを移行
- ✅ グローバル状態管理からセッションベースの状態管理に変更
- ✅ マークダウンベースのUI定義に移行
- ✅ RAG（検索拡張生成）機能を削除してシンプル化
- ✅ ベクトルDB（ChromaDB）関連の依存関係を削除
- ✅ ドキュメント処理（PDF、DOCX）機能を削除
- ✅ 不要なパッケージを削除（pandas、numpy、fastapi等）
- ✅ `langchain-classic`を使用して最新バージョンに対応
- ✅ 関数名をリファクタリング（`initialize_agent_executor` → `initialize_llm_chain`）
- ✅ プロンプトテンプレートの変数エスケープ問題を修正

### セキュリティと制約

アプリケーションには以下の安全性制約が組み込まれています：

1. **デバイス制限**: fioコマンドは`/dev/nvme0n1`のみに実行
2. **時間制限**: fioの実行時間は最大10秒
3. **危険なコマンドの拒否**: フォーマット等の危険な操作は拒否
4. **単一コマンド**: 複雑なスクリプトではなく単一のbashコマンドのみ生成

## トラブルシューティング

### インポートエラー

```bash
# Pythonキャッシュをクリア
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

### ポートが使用中

```bash
# 既存のプロセスを停止
pkill -f "python main.py"

# または別のポートを使用（main.pyのport設定を変更）
```

### Taipyバージョン問題

このプロジェクトはTaipy 3.0以上を必要とします。
互換性の問題が発生した場合は、最新版へのアップグレードを試してください：

```bash
pip install --upgrade taipy
```

## ライセンス

このプロジェクトは社内利用を目的としています。
