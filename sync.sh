#!/usr/bin/env bash
# 一键：飞书 -> data.js -> 压缩图片（本地用）
# 用法：先 export 四个环境变量，再 ./sync.sh
#   export FEISHU_APP_ID=cli_xxx
#   export FEISHU_APP_SECRET=xxx
#   export FEISHU_APP_TOKEN=xxx
#   export FEISHU_TABLE_ID=tblxxx
#   ./sync.sh
# 首次会自动创建 .venv 并装 Pillow（仅一次）；之后自动复用。
set -e
cd "$(dirname "$0")"

: "${FEISHU_APP_ID:?未设置 FEISHU_APP_ID，请先 export 飞书四个环境变量}"
: "${FEISHU_APP_SECRET:?未设置 FEISHU_APP_SECRET}"
: "${FEISHU_APP_TOKEN:?未设置 FEISHU_APP_TOKEN}"
: "${FEISHU_TABLE_ID:?未设置 FEISHU_TABLE_ID}"

# 选用 python：优先项目内 .venv，否则系统 python3
if [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
else
  PY=python3
fi

# 没有 Pillow 就建一个一次性 venv 装上
if ! "$PY" -c "import PIL" 2>/dev/null; then
  echo "首次使用：创建 .venv 并安装 Pillow（约 10 秒）..."
  python3 -m venv .venv
  .venv/bin/python -m pip install -q --upgrade pip Pillow
  PY=.venv/bin/python
fi

"$PY" sync_feishu.py
"$PY" optimize_images.py
echo "✅ 已生成 data.js 并压缩 images/，本地双击 index.html 或刷新预览即可看效果"
