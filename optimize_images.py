#!/usr/bin/env python3
"""压缩 images/ 下的截图，原地覆盖，保持文件名与后缀不变。

- 宽度超过 MAX_W 的图缩放到 MAX_W（竖图优先，画廊展示足够清晰）
- PNG：铺白底去透明 -> 256 色调色板 -> optimize，体积小且文字清晰
- JPG：resize + quality 压缩
部署前和本地 sync 时都会调用，用户只需往 images/ 丢原图即可。
"""
import os
import sys
from PIL import Image

IMAGES_DIR = "images"
MAX_W = 1080


def optimize_file(path):
    try:
        im = Image.open(path)
    except Exception as e:
        print(f"  ⚠️  跳过 {path}：{e}")
        return 0, 0

    before = os.path.getsize(path)

    # 缩放：仅当宽度超限
    if im.width > MAX_W:
        h = int(im.height * MAX_W / im.width)
        im = im.resize((MAX_W, h), Image.LANCZOS)

    lower = path.lower()
    if lower.endswith(".png"):
        # 去透明：贴到白底，再量化成 256 色 PNG（体积小、文字清晰）
        if im.mode in ("RGBA", "LA", "P"):
            if im.mode != "P":
                im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            mask = im.split()[-1] if im.mode in ("RGBA", "LA") else None
            bg.paste(im, mask=mask)
            im = bg
        else:
            im = im.convert("RGB")
        im = im.convert("P", palette=Image.ADAPTIVE, colors=256)
        im.save(path, optimize=True)
    elif lower.endswith((".jpg", ".jpeg")):
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.save(path, "JPEG", quality=82, optimize=True)
    else:
        return before, before

    after = os.path.getsize(path)
    return before, after


def main():
    if not os.path.isdir(IMAGES_DIR):
        print(f"未找到 {IMAGES_DIR}/ 目录，跳过压缩")
        return
    total_before = total_after = 0
    count = 0
    print(f"🗜️  压缩 {IMAGES_DIR}/ 下的图片（最大宽度 {MAX_W}px）...")
    for name in sorted(os.listdir(IMAGES_DIR)):
        if name.lower().endswith((".png", ".jpg", ".jpeg")):
            p = os.path.join(IMAGES_DIR, name)
            b, a = optimize_file(p)
            count += 1
            total_before += b
            total_after += a
            if b != a:
                print(f"  ✅ {name}: {b//1024}KB -> {a//1024}KB  (-{(1-a/b)*100:.0f}%)")
    if count == 0:
        print("  没有需要压缩的图片")
        return
    saved = total_before - total_after
    pct = (saved / total_before * 100) if total_before else 0
    print(f"📦 共 {count} 张，{total_before//1024}KB -> {total_after//1024}KB，省 {saved//1024}KB (-{pct:.0f}%)")


if __name__ == "__main__":
    try:
        from PIL import Image  # noqa
    except ImportError:
        print("⚠️  未安装 Pillow，跳过压缩（部署流程会自动安装）。本地用：pip install Pillow")
        sys.exit(0)
    main()
