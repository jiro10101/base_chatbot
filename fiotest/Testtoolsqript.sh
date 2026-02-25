#!/bin/bash

# ==========================================
# Testtoolsqript.sh
# 概要: 引数を受け取り、指定されたテストスクリプトを実行するラッパー
#[実施フォーマット]
#Testtoolsqript.sh [FWver] [実施script] [実施モデル] [実施環境]
#[例]
#Testtoolsqript.sh 1.00 rand_read_simple.sh ModelA 100.67.161.104
# ==========================================

# ------------------------------------------
# 1. 引数の取得 (将来の拡張用)
# ------------------------------------------
# 将来的にこれらの変数を判定条件などに使用できます
FW_VER="$1"       # FWバージョン (例: 1.00)
TARGET_SCRIPT="$2" # 実行するスクリプト (例: rand_read_simple.sh)
MODEL="$3"        # 実施モデル (例: ModelA)
ENV_ADDRESS="$4"  # 実施環境/IP (例: 100.67.161.104)

# 引数が足りない場合の簡易チェック（オプション）
if [ -z "$TARGET_SCRIPT" ]; then
    echo "Usage: $0 [FWver] [実施script] [実施モデル] [実施環境]"
    echo "Example: $0 1.00 rand_read_simple.sh ModelA 100.67.161.104"
    exit 1
fi

# ------------------------------------------
# 2. 環境変数のエクスポート (子スクリプトで使用可能にする)
# ------------------------------------------
export FW_VER
export MODEL
export ENV_ADDRESS

# デバッグ出力
echo "FW Ver: $FW_VER, Model: $MODEL, Env: $ENV_ADDRESS"

# ------------------------------------------
# 3. 指定スクリプトの実行
# ------------------------------------------

# スクリプトパスの解決 (絶対パス、相対パス、カレントディレクトリに対応)
SCRIPT_PATH=""

if [ -f "$TARGET_SCRIPT" ]; then
    # 絶対パスまたは相対パスで直接指定された場合
    SCRIPT_PATH="$TARGET_SCRIPT"
elif [ -f "./$TARGET_SCRIPT" ]; then
    # カレントディレクトリ内のファイル
    SCRIPT_PATH="./$TARGET_SCRIPT"
else
    echo "Error: Script file '$TARGET_SCRIPT' not found."
    echo "Tried: $TARGET_SCRIPT and ./$TARGET_SCRIPT"
    exit 1
fi

# 実行権限がない場合は付与する (必要に応じて)
if [ ! -x "$SCRIPT_PATH" ]; then
    echo "Warning: Making $SCRIPT_PATH executable."
    chmod +x "$SCRIPT_PATH"
fi

echo "Starting execution of: $SCRIPT_PATH ..."
echo "----------------------------------------"

# --- スクリプト実行 ---
"$SCRIPT_PATH"

# 実行結果のステータスコードを保存
RESULT=$?

echo "----------------------------------------"
echo "Finished execution. (Exit Code: $RESULT)"
exit $RESULT

