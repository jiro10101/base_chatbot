"""
このファイルは、固定の文字列や数値などのデータを変数として一括管理するファイルです。
"""

############################################################
# 共通変数の定義
############################################################

# ==========================================
# 画面表示系
# ==========================================
APP_NAME = "Linux、fioアシスタント"
APP_BOOT_MESSAGE = "アプリが起動されました。"
CHAT_INPUT_HELPER_TEXT = "こちらからメッセージを送信してください。"
USER_ICON_FILE_PATH = "./images/user_icon.jpg"
AI_ICON_FILE_PATH = "./images/ai_icon.jpg"
WARNING_ICON = ":material/warning:"
ERROR_ICON = ":material/error:"
SPINNER_TEXT = "回答生成中..."



# ==========================================
# ログ出力系
# ==========================================
LOG_DIR_PATH = "./logs"
LOGGER_NAME = "ApplicationLog"
LOG_FILE = "application.log"


# ==========================================
# LLM設定系
# ==========================================
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.5


# ==========================================
# トークン関連
# ==========================================
MAX_ALLOWED_TOKENS = 1000
ENCODING_KIND = "cl100k_base"






# ==========================================
# プロンプトテンプレート
# ==========================================
SYSTEM_PROMPT_INQUIRY = """
あなたは Linux (Ubuntu 24.04) の専門家アシスタントです。
あなたの唯一の役割は、ユーザーの自然言語による指示を、指定された制約条件に厳密に従った単一のLinux bashコマンドに変換することです。

# 厳格なルール (LLMへの指示)
1.  **コマンドのみ**: 実行可能なbashコマンドのみを生成してください。
2.  **説明不要**: 説明、謝罪、挨拶、追加のテキスト（例: 「コマンドは以下の通りです」）は一切禁止します。
3.  **単一コマンド**: 1行のbashコマンドのみを返してください。


# 制約条件 (仕様書要件)
1.  **fioの制約 (最重要)**:
    * `fio` コマンドを生成する場合、対象デバイス (`--filename`) は必ず `/dev/nvme0n1` を使用してください。
    * `fio` の測定時間 (`--runtime`) は、必ず 10秒以下に設定してください。
    * `fio` を実行する際は、必ず `--name=test` `--filename=/dev/nvme0n1` `--direct=1` `--time_based` `--runtime=[10秒以下の数値]` を含めてください。
    * 読み取り/書き込みの指定がない場合は、安全な `--rw=read` (読み取り専用) を優先してください。
    * 例: `fio --name=test --filename=/dev/nvme0n1 --direct=1 --rw=randread --bs=4k --runtime=10 --time_based --group_reporting`

    
# 出力例 (Few-shot learning: LLMに良い例と悪い例を示す)
User: /dev/nvme0n1 に4kブロックサイズでランダムリードのテストを5秒間実行して
You: fio --name=test --filename=/dev/nvme0n1 --direct=1 --rw=randread --bs=4k --runtime=5 --time_based --group_reporting

User: /dev/nvme0n1 のシーケンシャルライトを8kで10秒測定
You: fio --name=test --filename=/dev/nvme0n1 --direct=1 --rw=write --bs=8k --runtime=10 --time_based --group_reporting

User: ディスクの空き容量を見せて
You: df -h

"""



# ==========================================
# エラー・警告メッセージ
# ==========================================
COMMON_ERROR_MESSAGE = "このエラーが繰り返し発生する場合は、管理者にお問い合わせください。"
INITIALIZE_ERROR_MESSAGE = "初期化処理に失敗しました。"
CONVERSATION_LOG_ERROR_MESSAGE = "過去の会話履歴の表示に失敗しました。"
MAIN_PROCESS_ERROR_MESSAGE = "ユーザー入力に対しての処理に失敗しました。"
DISP_ANSWER_ERROR_MESSAGE = "回答表示に失敗しました。"
INPUT_TEXT_LIMIT_ERROR_MESSAGE = f"入力されたテキストの文字数が受付上限値（{MAX_ALLOWED_TOKENS}）を超えています。受付上限値を超えないよう、再度入力してください。"



# ==========================================
# スタイリング
# ==========================================
STYLE = """
<style>
    .stHorizontalBlock {
        margin-top: -14px;
    }
    .stChatMessage + .stHorizontalBlock {
        margin-left: 56px;
    }
    .stChatMessage + .stHorizontalBlock .stColumn:nth-of-type(2) {
        margin-left: -24px;
    }
    @media screen and (max-width: 480px) {
        .stChatMessage + .stHorizontalBlock {
            flex-wrap: nowrap;
            margin-left: 56px;
        }
        .stChatMessage + .stHorizontalBlock .stColumn:nth-of-type(2) {
            margin-left: -206px;
        }
    }
</style>
"""