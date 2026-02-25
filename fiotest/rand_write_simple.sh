#!/usr/bin/env bash
set -euo pipefail
# ================================================
# ランダムライト試験（4k, QD64, 4jobs）
# ・目的：4Kランダム書込みのIOPS/レイテンシ測定
# ・注意：書込み試験は破壊的です（データ消去）。
# ================================================
TEST_NAME="randwrite"
# ========= 共通設定 =========
DEV="/dev/nvme0n1"              # 対象SSDのブロックデバイス
RUNTIME="10"                    # 測定時間(秒)
OUTDIR="results"                # 出力ディレクトリ
IOENGINE="io_uring"             # I/Oエンジン
PRECON="0"                      # プレコン有効化(1=有効, 0=無効)※破壊的
IDLE_SEC="0"                    # プレコン後のアイドル時間（秒）
WARMUP_SEC="0"                  # ウォームアップ時間(秒)
mkdir -p "$OUTDIR"
TS="$(date +%Y%m%d_%H%M%S)"
# Testtoolsqript.sh から渡された引数を含むファイル名を生成
if [[ -n "${FW_VER:-}" && -n "${MODEL:-}" && -n "${ENV_ADDRESS:-}" ]]; then
  JSON_OUT="$OUTDIR/${TS}_${TEST_NAME}_FW${FW_VER}_${MODEL}_${ENV_ADDRESS}.json"
else
  JSON_OUT="$OUTDIR/${TS}_${TEST_NAME}.json"
fi
# ========= プレコン（破壊的） =========
if [[ "$PRECON" == "1" ]]; then
  echo "⚠️ プレコンを実行します：SSD全域に128KiB SeqWriteを2パス（データ消去）。DEV=$DEV"
  # パス1
  fio --name=precon1         --filename="$DEV" --ioengine="$IOENGINE" --direct=1         --rw=write --bs=128k --iodepth=32 --numjobs=1         --time_based=0 --size=100% --group_reporting=1
  # パス2
  fio --name=precon2         --filename="$DEV" --ioengine="$IOENGINE" --direct=1         --rw=write --bs=128k --iodepth=32 --numjobs=1         --time_based=0 --size=100% --group_reporting=1
  echo "プレコン完了。アイドル ${IDLE_SEC}s 待機します…"
  sleep "$IDLE_SEC"
else
  echo "PRECON=0 のためプレコンは実行しません。"
fi
# ========= ウォームアップ =========
# echo "ウォームアップ ${WARMUP_SEC}s 実行中…"
# fio --name=warmup     --filename="$DEV" --ioengine="$IOENGINE" --direct=1     --time_based=1 --runtime="$WARMUP_SEC"     --rw=randread --bs=4k --iodepth=16 --numjobs=1     --group_reporting=1 --output=/dev/null --output-format=normal
echo "=== RandWrite を ${RUNTIME}s 実行します…（DEV=$DEV）"
fio --name=randwrite     --filename="$DEV" --ioengine="$IOENGINE" --direct=1     --time_based=1 --runtime="$RUNTIME"     --rw=randwrite --bs=4k --iodepth=64 --numjobs=4     --group_reporting=1     --output="$JSON_OUT" --output-format=json
RC=$?
if [[ $RC -ne 0 ]]; then
  echo "fioがエラー終了しました（code=$RC）" >&2
  exit $RC
fi

# ========= 簡易サマリ（jqがある場合） =========
if command -v jq >/dev/null 2>&1; then
  echo "# Summary (job, MB/s, IOPS, mean_lat_ns, p99_ns)"
  jq -r '.jobs[] | [
    .jobname,
    ((.read.bw_bytes // 0) + (.write.bw_bytes // 0)) / 1000000,
    (.read.iops // .write.iops // 0),
    (.read.clat_ns.mean // .write.clat_ns.mean // 0),
    (.read.clat_ns.percentile["99.000000"] // .write.clat_ns.percentile["99.000000"] // 0)
  ] | @tsv' "$JSON_OUT"
else
  echo "(ヒント) sudo apt-get install -y jq を入れるとサマリ表示できます。"
fi

echo "出力ファイル: $JSON_OUT"
