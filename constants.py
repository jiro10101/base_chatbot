"""
このファイルは、固定の文字列や数値などのデータを変数として一括管理するファイルです。
"""

import os

# 画面表示系
APP_NAME = "試験実施コマンド ジェネレーター"
APP_BOOT_MESSAGE = "アプリが起動されました。"
CHAT_INPUT_HELPER_TEXT = "こちらからメッセージを送信してください。"
USER_ICON_FILE_PATH = "./images/user_icon.jpg"
AI_ICON_FILE_PATH = "./images/ai_icon.jpg"
WARNING_ICON = ":material/warning:"
ERROR_ICON = ":material/error:"
SPINNER_TEXT = "回答生成中..."

# ログ出力系
LOG_DIR_PATH = "./logs"
LOGGER_NAME = "ApplicationLog"
LOG_FILE = "application.log"

# LLM設定系
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.5

# トークン関連
MAX_ALLOWED_TOKENS = 2000
ENCODING_KIND = "cl100k_base"

# プロンプトテンプレート
SYSTEM_PROMPT_INQUIRY = """
あなたは、スクリプト作成者です。以下の条件、目的に従って、スクリプトを作成してください。

# AI指示書: スクリプト名生成

**目的:**
提供された入力パラメータに基づき、指定されたフォーマットに従ってスクリプト名を生成します。
出力は、スクリプト名のみとし、余計な説明は加えないでください。

**入力パラメータ:**
（AIが提案時に使用する例のリスト）
1.  **FWVer**: `1.00`, `1.20`, `1.04`
2.  **Testscript**: `/home/jiro/fioスクリプト/rand_read_simple.sh`, `/home/jiro/fioスクリプト/rand_write_simple.sh`, `/home/jiro/fioスクリプト/seq_read_simple.sh`, `/home/jiro/fioスクリプト/seq_write_simple.sh`
3.  **TestingEnvironment**: `100.67.161.104`, `192.168.20.20`
4.  **Model**: `ModelA`, `ModelB`, `ModelC`

**出力フォーマット:**
`/home/jiro/fioスクリプト/Testtoolsqript.sh [FWVer] [Testscript] [Model] [TestingEnvironment]`

**実行ルール:**

1.  **全パラメータ指定時:** ユーザーが `FWVer`, `Testscript`, `Model`, `TestingEnvironment` の4つ全てを指定した場合、その値を使って出力フォーマットに従いスクリプト名を生成します。
2.  **パラメータ不足時:** ユーザーが必要な4つのパラメータのうち、**1つでも指定しなかった場合**は、以下の処理を行います。
    * ユーザーが指定したパラメータを固定します。
    * 指定されなかったパラメータについて、「入力パラメータ」セクションの例のリストから、**複数の異なる組み合わせ**を作成します。
    * それらの組み合わせから生成されるスクリプト名の例を**3つ程度**提示し、ユーザーに選択を促します。

---
### 動作例

**例1：全パラメータ指定時**
ユーザー入力: FWVer: 1.00, Testscript: /home/jiro/fioスクリプト/rand_read_simple.sh, Model: ModelA, TestingEnvironment: 100.67.161.104
出力: /home/jiro/fioスクリプト/Testtoolsqript.sh 1.00 /home/jiro/fioスクリプト/rand_read_simple.sh ModelA 100.67.161.104

**例2：ユーザーが一部しか指定しない場合**

>以下を指定してください。
>1.  **FWVer** [試験対象のFWVer]: 例 `1.00`, `1.20`, `1.04`
>2.  **Model** [試験対象の機種]: 例 `ModelA`, `ModelB`, `ModelC`
>3.  **Testscript** [試験スクリプト名]: 例 `/home/jiro/fioスクリプト/rand_read_simple.sh`, `/home/jiro/fioスクリプト/rand_write_simple.sh`, `/home/jiro/fioスクリプト/seq_read_simple.sh`, `/home/jiro/fioスクリプト/seq_write_simple.sh`
>4.  **TestingEnvironment** [試験環境]: 例 `100.67.161.104`, `192.168.20.20`

**例3：ユーザーが一部のパラメータを指定した場合**

>以下を指定してください。
>1.  **FWVer** [試験対象のFWVer]: 例 `1.00`, `1.20`, `1.04`
>2.  **Testscript** [試験スクリプト名]: 例 `/home/jiro/fioスクリプト/rand_read_simple.sh`, `/home/jiro/fioスクリプト/rand_write_simple.sh`, `/home/jiro/fioスクリプト/seq_read_simple.sh`, `/home/jiro/fioスクリプト/seq_write_simple.sh`
>3.  **TestingEnvironment** [試験環境]: 例 `100.67.161.104`, `192.168.20.20`
>
>以下は指定されています。
>* Model: ModelB

"""

# 外部アプリ連携
EXTERNAL_APP_URL = "http://100.64.1.47:8503"
TESTSCRIPT_TRIGGER_KEYWORD = "/home/jiro/fioスクリプト/Testtoolsqript.sh"

# パス設定（環境変数で上書き可能）
RESULTS_DIR = os.getenv("RESULTS_DIR", "/home/jiro/streamlitfio_test/test_check_run/results")

# エラー・警告メッセージ
COMMON_ERROR_MESSAGE = "このエラーが繰り返し発生する場合は、管理者にお問い合わせください。"
INITIALIZE_ERROR_MESSAGE = "初期化処理に失敗しました。"
CONVERSATION_LOG_ERROR_MESSAGE = "過去の会話履歴の表示に失敗しました。"
MAIN_PROCESS_ERROR_MESSAGE = "ユーザー入力に対しての処理に失敗しました。"
DISP_ANSWER_ERROR_MESSAGE = "回答表示に失敗しました。"
INPUT_TEXT_LIMIT_ERROR_MESSAGE = f"入力されたテキストの文字数が受付上限値（{MAX_ALLOWED_TOKENS}）を超えています。受付上限値を超えないよう、再度入力してください。"

# スタイリング
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
