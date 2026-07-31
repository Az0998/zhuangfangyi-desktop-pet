"""通用角色包构建：anime/pixel 全身图 → 不裁头英雄骨骼 + parts。

用法:
  python tools/build_character_pack.py luoxi
  python tools/build_character_pack.py zhuangfangyi
  python tools/build_character_pack.py exusiai
  python tools/build_character_pack.py --all
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
CHARS = ROOT / "characters"
ASSET_DIRS = [
    Path(r"C:\Users\zsj\.cursor\projects\d-deep-learning-code-zhuangfangyi-desktop-pet\assets"),
    ROOT / "assets",
]

# 角色 → 源图文件名（优先 clean）
SOURCES = {
    "luoxi": {
        "anime": ["luoxi-anime-fullbody-v2.png", "luoxi-anime-fullbody.png"],
        "pixel": ["luoxi-pixel-clean.png", "luoxi-pixel-fullbody-v2.png", "luoxi-pixel-fullbody.png"],
    },
    "zhuangfangyi": {
        "anime": ["zhuangfangyi-anime-fullbody.png"],
        "pixel": ["zhuangfangyi-pixel-clean.png"],
    },
    "exusiai": {
        "anime": ["exusiai-anime-fullbody.png"],
        "pixel": ["exusiai-pixel-clean.png"],
    },
}


def find_asset(names: list[str]) -> Path | None:
    for name in names:
        for base in ASSET_DIRS:
            p = base / name
            if p.exists():
                return p
    return None


def remove_bg(img: Image.Image, *, chroma: tuple[int, int, int] | None = None) -> Image.Image:
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()

    def is_bg(r, g, b, a) -> bool:
        if a < 10:
            return True
        if chroma is not None:
            cr, cg, cb = chroma
            if abs(r - cr) + abs(g - cg) + abs(b - cb) < 120:
                return True
        mx, mn = max(r, g, b), min(r, g, b)
        if mx >= 232 and (mx - mn) <= 40:
            return True
        if r > 208 and g > 208 and b > 208 and (mx - mn) < 24:
            return True
        return False

    if chroma is not None:
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if is_bg(r, g, b, a):
                    px[x, y] = (0, 0, 0, 0)

    visited = [[False] * w for _ in range(h)]
    stack = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (0, h // 2), (w - 1, h // 2)]
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            continue
        visited[y][x] = True
        r, g, b, a = px[x, y]
        if not is_bg(r, g, b, a):
            continue
        px[x, y] = (0, 0, 0, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return img


def heal_dark_holes(img: Image.Image, max_neighbors: int = 5) -> Image.Image:
    """填补孤立近黑透明洞（像素伪影）。"""
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    out = img.copy()
    opx = out.load()
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            r, g, b, a = px[x, y]
            # 近黑且周围有彩色 → 当伪影修掉
            if a > 20 and r < 28 and g < 28 and b < 28:
                cols = []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        rr, gg, bb, aa = px[x + dx, y + dy]
                        if aa > 40 and (rr > 40 or gg > 40 or bb > 40):
                            cols.append((rr, gg, bb, aa))
                if len(cols) >= max_neighbors:
                    # 邻域平均色
                    ar = sum(c[0] for c in cols) // len(cols)
                    ag = sum(c[1] for c in cols) // len(cols)
                    ab = sum(c[2] for c in cols) // len(cols)
                    aa = sum(c[3] for c in cols) // len(cols)
                    opx[x, y] = (ar, ag, ab, aa)
            # 完全透明洞夹在实体中
            if a < 15:
                cols = []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        rr, gg, bb, aa = px[x + dx, y + dy]
                        if aa > 80 and not (rr < 25 and gg < 25 and bb < 25):
                            cols.append((rr, gg, bb, aa))
                if len(cols) >= 6:
                    ar = sum(c[0] for c in cols) // len(cols)
                    ag = sum(c[1] for c in cols) // len(cols)
                    ab = sum(c[2] for c in cols) // len(cols)
                    opx[x, y] = (ar, ag, ab, 255)
    return out


def trim(img: Image.Image, pad: int = 4) -> Image.Image:
    bbox = img.getbbox()
    if not bbox:
        return img
    l, t, r, b = bbox
    return img.crop((max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad)))


def sharpen(img: Image.Image, amount: float = 1.2) -> Image.Image:
    return ImageEnhance.Contrast(ImageEnhance.Sharpness(img).enhance(amount)).enhance(1.05)


def make_blush(w: int = 90, h: int = 36) -> Image.Image:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((4, 8, 34, 30), fill=(255, 120, 150, 95))
    d.ellipse((w - 34, 8, w - 4, 30), fill=(255, 120, 150, 95))
    return img.filter(ImageFilter.GaussianBlur(1.0))


def make_empty(w: int = 8, h: int = 8) -> Image.Image:
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def write_hero_skeleton(path: Path, body: Image.Image, *, pad_top=28, pad_bottom=18, pad_side=56) -> None:
    bw, bh = body.size
    width = bw + pad_side * 2
    height = bh + pad_top + pad_bottom
    skel = {
        "width": width,
        "height": height,
        "origin": {"x": width // 2, "y": height - pad_bottom},
        "bones": [
            {"name": "root", "parent": None, "x": 0, "y": 0, "rotation": 0, "length": 0, "z": 0},
            {"name": "tail", "parent": "root", "x": -bw * 0.2, "y": -bh * 0.32, "rotation": -10, "length": 36, "z": 5},
            {
                "name": "body",
                "parent": "root",
                "x": 0,
                "y": 0,
                "rotation": 0,
                "length": bh,
                "z": 20,
                "part": "body",
                "pivot_x": bw // 2,
                "pivot_y": bh - 4,
            },
            {"name": "ear_l", "parent": "body", "x": -bw * 0.16, "y": -bh * 0.76, "rotation": -8, "length": 14, "z": 40},
            {"name": "ear_r", "parent": "body", "x": bw * 0.16, "y": -bh * 0.76, "rotation": 8, "length": 14, "z": 40},
            {"name": "torso", "parent": "body", "x": 0, "y": -bh * 0.34, "rotation": 0, "length": 10, "z": 21},
            {"name": "head", "parent": "body", "x": 0, "y": -bh * 0.7, "rotation": 0, "length": 10, "z": 30},
            {"name": "hood", "parent": "head", "x": 0, "y": 0, "rotation": 0, "length": 4, "z": 29},
            {"name": "face", "parent": "head", "x": 0, "y": 8, "rotation": 0, "length": 4, "z": 31},
            {"name": "eyes", "parent": "face", "x": 0, "y": 0, "rotation": 0, "length": 2, "z": 32},
            {"name": "arm_l", "parent": "body", "x": -bw * 0.26, "y": -bh * 0.42, "rotation": 0, "length": 18, "z": 15},
            {"name": "arm_r", "parent": "body", "x": bw * 0.26, "y": -bh * 0.42, "rotation": 0, "length": 18, "z": 15},
            {"name": "leg_l", "parent": "root", "x": -bw * 0.08, "y": -bh * 0.08, "rotation": 0, "length": 16, "z": 10},
            {"name": "leg_r", "parent": "root", "x": bw * 0.08, "y": -bh * 0.08, "rotation": 0, "length": 16, "z": 10},
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(skel, ensure_ascii=False, indent=2), encoding="utf-8")


def anime_to_pixel(anime_body: Image.Image, target_h: int = 180) -> Image.Image:
    """从干净动漫全身量化出清晰像素风，避免 AI 像素黑块。"""
    img = anime_body.convert("RGBA")
    # 先缩到低分辨率逻辑像素，再放大
    logical_h = 64
    scale = logical_h / max(1, img.height)
    logical = img.resize((max(8, int(img.width * scale)), logical_h), Image.Resampling.LANCZOS)
    # 量化调色板（保留透明）
    rgba = logical
    alpha = rgba.getchannel("A")
    rgb = rgba.convert("RGB").quantize(colors=48, method=Image.Quantize.MEDIANCUT).convert("RGB")
    logical = Image.merge(
        "RGBA",
        (*rgb.split(), alpha.point(lambda a: 255 if a > 40 else 0)),
    )
    # 清掉孤立深色噪点
    logical = heal_dark_holes(logical, max_neighbors=4)
    logical = heal_dark_holes(logical, max_neighbors=3)
    out_h = target_h
    scale2 = out_h / logical.height
    return logical.resize(
        (max(1, int(logical.width * scale2)), out_h),
        Image.Resampling.NEAREST,
    )


def build_variant(char_id: str, style: str, src: Path, target_h: int, *, anime_body: Image.Image | None = None) -> Image.Image:
    out = CHARS / char_id / "variants" / style / "parts"
    out.mkdir(parents=True, exist_ok=True)

    if style == "pixel" and anime_body is not None:
        body = anime_to_pixel(anime_body, target_h=target_h)
        src_name = "from-anime-quantize"
    else:
        img = Image.open(src)
        chroma = (255, 0, 255) if style == "pixel" else None
        body = remove_bg(img, chroma=chroma)
        body = trim(body)
        if style == "anime":
            body = sharpen(body, 1.22)
            resample = Image.Resampling.LANCZOS
        else:
            body = heal_dark_holes(body)
            body = heal_dark_holes(body)
            resample = Image.Resampling.NEAREST
        scale = target_h / max(1, body.height)
        body = body.resize((max(1, int(body.width * scale)), target_h), resample)
        if style == "pixel":
            body = heal_dark_holes(body)
        src_name = src.name

    body.save(out / "body.png")
    for name in ("head", "hood", "face", "eyes", "ear_l", "ear_r", "torso", "arm_l", "arm_r", "leg_l", "leg_r", "tail"):
        make_empty().save(out / f"{name}.png")
    make_blush().save(out / "blush.png")
    head = trim(body.crop((0, 0, body.width, int(body.height * 0.48))))
    head.save(out / "head.png")

    pad = (28, 18, 56) if style == "anime" else (20, 12, 40)
    write_hero_skeleton(
        CHARS / char_id / "variants" / style / "skeleton.json",
        body,
        pad_top=pad[0],
        pad_bottom=pad[1],
        pad_side=pad[2],
    )
    print(f"  [{char_id}/{style}] {body.size} ← {src_name}")

    if style == "anime":
        legacy = CHARS / char_id / "parts"
        legacy.mkdir(exist_ok=True)
        for p in out.glob("*.png"):
            shutil.copy2(p, legacy / p.name)
    return body


def ensure_shared_animations(char_id: str) -> None:
    shared = CHARS / "_shared" / "animations.json"
    dest = CHARS / char_id / "animations.json"
    if shared.exists():
        shutil.copy2(shared, dest)
        print(f"  animations ← shared for {char_id}")


def build_character(char_id: str) -> None:
    if char_id not in SOURCES:
        raise SystemExit(f"unknown character: {char_id}")
    print(f"构建 {char_id} …")
    anime_src = find_asset(SOURCES[char_id]["anime"])
    pixel_src = find_asset(SOURCES[char_id]["pixel"])
    if not anime_src and not pixel_src:
        raise SystemExit(f"找不到 {char_id} 源图")
    anime_body = None
    if anime_src:
        anime_body = build_variant(char_id, "anime", anime_src, 300)
    # 像素版优先用动漫量化（更干净）；无动漫时才用 pixel 源图
    if anime_body is not None:
        build_variant(char_id, "pixel", pixel_src or anime_src, 180, anime_body=anime_body)
    elif pixel_src:
        build_variant(char_id, "pixel", pixel_src, 180)
    ensure_shared_animations(char_id)
    anime_skel = CHARS / char_id / "variants" / "anime" / "skeleton.json"
    if anime_skel.exists():
        shutil.copy2(anime_skel, CHARS / char_id / "skeleton.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("characters", nargs="*", help="luoxi zhuangfangyi exusiai")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    ids = list(SOURCES) if args.all or not args.characters else args.characters
    for cid in ids:
        build_character(cid)
    print("完成。")


if __name__ == "__main__":
    main()
