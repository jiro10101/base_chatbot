"""
このファイルは、固定の文字列や数値などのデータを変数として一括管理するファイルです。
"""

############################################################
# 共通変数の定義
############################################################

# ==========================================
# 画面表示系
# ==========================================
APP_NAME = "Redmineチケット文言案ジェネレーター"
APP_BOOT_MESSAGE = "アプリが起動されました。"
CHAT_INPUT_HELPER_TEXT = "Redmine番号や要求を入力してください"
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
# Redmine API設定
# ==========================================
REDMINE_URL = "http://your-redmine-url.com"  # Redmine URLを設定
REDMINE_API_KEY = ""  # .envから読み込む


# ==========================================
# トークン関連
# ==========================================
MAX_ALLOWED_TOKENS = 1000
ENCODING_KIND = "cl100k_base"






# ==========================================
# プロンプトテンプレート
# ==========================================
SYSTEM_PROMPT_INQUIRY = """
あなたは、Redmineチケットの文言案を作成する専門アシスタントです。

# 役割
ユーザーから提供されたRedmineチケット情報を基に、新しいチケットの文言案を作成してください。

# 参照するRedmineチケット情報
{redmine_info}

# 出力形式
以下の形式で、新しいチケットの文言案を作成してください：

**題名:**
[簡潔で分かりやすいタイトル]

**説明:**
[詳細な説明文]
- 背景
- 目的
- 実施内容
- 期待される結果

**注意事項:**
[必要に応じて注意事項を記載]

# ルール
1. 参照チケットの情報を踏まえた上で、新しいチケットとして適切な内容を提案してください
2. 具体的で実行可能な内容にしてください
3. 必要に応じて、参照チケットから関連する情報を引用してください
4. 専門用語は適切に使用し、必要に応じて説明を加えてください
"""


SYSTEM_PROMPT_NO_REDMINE = """
あなたは、Redmineチケットの文言案を作成する専門アシスタントです。

ユーザーの要求に基づいて、新しいRedmineチケットの文言案を作成してください。

# 出力形式
**題名:**
[簡潔で分かりやすいタイトル]

**説明:**
[詳細な説明文]
- 背景
- 目的
- 実施内容
- 期待される結果

**注意事項:**
[必要に応じて注意事項を記載]
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