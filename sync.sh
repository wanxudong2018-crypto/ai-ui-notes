#!/usr/bin/env bash
# 一键同步飞书 -> data.js（本地用）
# 用法：先 export 四个环境变量，再 ./sync.sh
#   export FEISHU_APP_ID=cli_xxx
#   export FEISHU_APP_SECRET=xxx
#   export FEISHU_APP_TOKEN=xxx
#   export FEISHU_TABLE_ID=tblxxx
#   ./sync.sh
set -e
cd "$(dirname "$0")"

: "${FEISHU_APP_ID:?未设置 FEISHU_APP_ID，请先 export 飞书四个环境变量}"
: "${FEISHU_APP_SECRET:?未设置 FEISHU_APP_SECRET}"
: "${FEISHU_APP_TOKEN:?未设置 FEISHU_APP_TOKEN}"
: "${FEISHU_TABLE_ID:?未设置 FEISHU_TABLE_ID}"

python3 sync_feishu.py
echo "✅ 已生成 data.js，本地双击 index.html 或刷新预览即可看效果"
