#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从飞书多维表格拉取截图数据，生成 data.js（前端画廊直接读取，无需后端）。

数据模型（一条记录 = 一个流程 / 单屏）
--------------------------------------
{
  "problem": "设计问题分类",
  "app": "App 名称",
  "platform": "平台(iOS/Android/Web)",
  "images": ["图片URL1", "图片URL2", ...],   # 多图流程；单屏就 1 张
  "steps":  ["步骤1说明", "步骤2说明", ...],   # 与 images 一一对应
  "note":   "整体说明（可选）"
}

飞书表格列建议（列名可在 config.json 的 columns 里改）
---------------------------------------------
问题分类 | App名称 | 平台 | 图片URLs | 步骤说明 | 整体说明
- 问题分类：单行文本 或 单选
- 平台：单选（iOS / Android / Web / macOS / 小程序）
- 图片URLs：文本字段，每行一个 URL（也支持「附件」字段直接传多张图）
- 步骤说明：文本字段，每行一句，与图片顺序对应
- 图片URL 建议用图床 / OSS / GitHub 图仓，别用飞书云空间外链（会失效）

使用方法
------
1. 飞书开放平台建「自建应用」，开通多维表格权限（bitable:app、bitable:app:readonly）。
2. 把该多维表格分享给这个应用（添加为协作者，至少可阅读）。
3. 复制 config.example.json 为 config.json，填入 app_id / app_secret / app_token / table_id。
4. 运行：python3 sync_feishu.py
   生成 data.js 后双击 index.html 预览，或部署到 Vercel / GitHub Pages。

仅用 Python 标准库，无需 pip install。
"""

import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

BASE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    path = os.path.join(BASE, "config.json")
    cfg = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    # 环境变量覆盖：密钥可不写入任何文件，仅在终端命令里提供
    env_map = {
        "FEISHU_APP_ID": "app_id",
        "FEISHU_APP_SECRET": "app_secret",
        "FEISHU_APP_TOKEN": "app_token",
        "FEISHU_TABLE_ID": "table_id",
    }
    for env_key, cfg_key in env_map.items():
        v = os.environ.get(env_key)
        if v:
            cfg[cfg_key] = v
    for required in ["app_id", "app_secret", "app_token", "table_id"]:
        if not cfg.get(required):
            sys.exit(
                "缺少 " + required + "：可在 config.json 填写，或用环境变量提供"
                "（FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_APP_TOKEN / FEISHU_TABLE_ID）。"
            )
    return cfg


def _post(url, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit("请求失败 " + url + "：" + e.read().decode("utf-8", "ignore"))


def get_token(app_id, app_secret):
    data = _post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        {"app_id": app_id, "app_secret": app_secret},
    )
    if data.get("code") != 0:
        sys.exit("获取 tenant_access_token 错误：" + str(data))
    return data["tenant_access_token"]


def fetch_records(token, app_token, table_id):
    out = []
    page_token = ""
    while True:
        url = (
            "https://open.feishu.cn/open-apis/bitable/v1/apps/"
            + app_token
            + "/tables/"
            + table_id
            + "/records?page_size=100"
        )
        if page_token:
            url += "&page_token=" + urllib.parse.quote(page_token)
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        if data.get("code") != 0:
            sys.exit("拉取记录失败：" + str(data))
        out.extend(data["data"]["items"])
        page_token = data["data"].get("page_token") or ""
        if not data["data"].get("has_more") or not page_token:
            break
    return out


def cell_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("text") or value.get("name") or ""
    if isinstance(value, list):
        return " / ".join(
            (v.get("text") or v.get("name") or "" if isinstance(v, dict) else str(v))
            for v in value
        )
    return str(value)


def cell_lines(value):
    """多值单元格 -> 字符串列表。支持：文本(按换行拆)、附件数组(取url)、单选/超链接(取text/name/link)。"""
    if value is None:
        return []
    if isinstance(value, str):
        return [ln.strip() for ln in value.split("\n") if ln.strip()]
    if isinstance(value, dict):
        t = value.get("url") or value.get("link") or value.get("text") or value.get("name") or ""
        return [t] if t else []
    if isinstance(value, list):
        out = []
        for v in value:
            if isinstance(v, dict):
                out.append(v.get("url") or v.get("link") or v.get("text") or v.get("name") or "")
            else:
                out.append(str(v))
        return [x for x in out if x]
    return [str(value)]


def main():
    cfg = load_config()
    cols = cfg.get("columns", {})
    problem_c = cols.get("problem", "问题分类")
    app_c = cols.get("app", "App名称")
    platform_c = cols.get("platform", "平台")
    images_c = cols.get("images", "图片URLs")
    steps_c = cols.get("steps", "步骤说明")
    note_c = cols.get("note", "整体说明")

    token = get_token(cfg["app_id"], cfg["app_secret"])
    records = fetch_records(token, cfg["app_token"], cfg["table_id"])

    items = []
    for rec in records:
        f = rec.get("fields", {})
        # 列名空格容错：去掉空格后做映射，无论飞书表头是「App名称」还是「App 名称」都能认
        fn = {k.replace(" ", ""): v for k, v in f.items()}
        def g(col):
            return fn.get(col.replace(" ", ""))

        items.append(
            {
                "problem": cell_text(g(problem_c)),
                "app": cell_text(g(app_c)),
                "platform": cell_text(g(platform_c)),
                "images": cell_lines(g(images_c)),
                "steps": cell_lines(g(steps_c)),
                "note": cell_text(g(note_c)),
            }
        )

    items = [i for i in items if i["app"] or i["problem"]]

    out_path = os.path.join(BASE, cfg.get("output", "data.js"))
    with open(out_path, "w", encoding="utf-8") as wf:
        wf.write("// 由 sync_feishu.py 生成，请勿手动编辑。\n")
        wf.write("window.APP_DATA = ")
        json.dump(items, wf, ensure_ascii=False, indent=2)
        wf.write(";\n")

    print("已生成 " + out_path + "，共 " + str(len(items)) + " 条记录。")


if __name__ == "__main__":
    main()
