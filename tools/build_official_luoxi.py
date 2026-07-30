"""
从 AI 重绘 / 官方参考图构建洛茜精细分层资源。

输入：Cursor assets 与 characters/luoxi/ref/
输出：variants/anime|pixel/parts + skeleton
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
CHAR = ROOT / "characters" / "luoxi"
REF = CHAR / "ref"
RAW = CHAR / "ai_raw"
ASSETS_CANDIDATES = [
    Path(r"C:\Users\zsj\.cursor\projects\d-deep-learning-code-zhuangfangyi-desktop-pet\assets"),
    ROOT / "assets",
]


def find_asset(name: str) -> Path | None:
    for base in ASSETS_CANDIDATES:
        p = base / name
        if p.exists():
            return p
    return None


def collect_raw() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    mapping = {
        "fullbody.png": "luoxi-anime-fullbody-v2.png",
        "fullbody_v1.png": "luoxi-anime-fullbody.png",
        "body_notail.png": "luoxi-anime-body-notail.png",
        "head_hood.png": "luoxi-part-head-hood.png",
        "tail.png": "luoxi-part-tail.png",
        "torso.png": "luoxi-part-torso.png",
        "arms.png": "luoxi-part-arms.png",
        "legs.png": "luoxi-part-legs.png",
        "ear.png": "luoxi-part-ear.png",
        "face_eyes.png": "luoxi-part-face-eyes.png",
        "pixel_full.png": "luoxi-pixel-fullbody-v2.png",
        "pixel_full_v1.png": "luoxi-pixel-fullbody.png",
    }
    for dst, src_name in mapping.items():
        src = find_asset(src_name)
        if src:
            shutil.copy2(src, RAW / dst)
            print(f"  raw ← {src_name}")


def remove_bg(
    img: Image.Image,
    *,
    chroma: tuple[int, int, int] | None = None,
    light_thresh: int = 235,
    sat_thresh: int = 28,
) -> Image.Image:
    """从四角洪水填充去背，避免误删角色深色区域。"""
    img = img.convert("RGBA")
    w, h = img.size
    pixels = img.load()

    def is_bg(r: int, g: int, b: int, a: int) -> bool:
        if a < 8:
            return True
        if chroma is not None:
            cr, cg, cb = chroma
            if abs(r - cr) + abs(g - cg) + abs(b - cb) < 100:
                return True
        mx, mn = max(r, g, b), min(r, g, b)
        # 仅浅色/灰白背景
        if mx >= light_thresh and (mx - mn) <= sat_thresh:
            return True
        if r > 210 and g > 210 and b > 210 and (mx - mn) < 22:
            return True
        return False

    # chroma 先扫一遍
    if chroma is not None:
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if is_bg(r, g, b, a):
                    pixels[x, y] = (0, 0, 0, 0)

    visited = [[False] * w for _ in range(h)]
    stack: list[tuple[int, int]] = []
    for pt in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (0, h // 2)):
        stack.append(pt)

    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            continue
        visited[y][x] = True
        r, g, b, a = pixels[x, y]
        if not is_bg(r, g, b, a):
            continue
        pixels[x, y] = (0, 0, 0, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return img


def trim(img: Image.Image, pad: int = 4) -> Image.Image:
    bbox = img.getbbox()
    if not bbox:
        return img
    l, t, r, b = bbox
    l = max(0, l - pad)
    t = max(0, t - pad)
    r = min(img.width, r + pad)
    b = min(img.height, b + pad)
    return img.crop((l, t, r, b))


def sharpen(img: Image.Image, amount: float = 1.15) -> Image.Image:
    img = ImageEnhance.Sharpness(img).enhance(amount)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    return img


def save_part(img: Image.Image, folder: Path, name: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    img.save(folder / f"{name}.png")
    print(f"  + {folder.parent.name}/{name}.png {img.size}")


def split_lr(img: Image.Image) -> tuple[Image.Image, Image.Image]:
    w, h = img.size
    mid = w // 2
    return trim(img.crop((0, 0, mid, h))), trim(img.crop((mid, 0, w, h)))


def make_blush(w: int = 120, h: int = 50) -> Image.Image:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 10, 48, 40), fill=(255, 120, 150, 100))
    d.ellipse((w - 48, 10, w - 8, 40), fill=(255, 120, 150, 100))
    return img.filter(ImageFilter.GaussianBlur(1.2))


def make_empty(w: int = 8, h: int = 8) -> Image.Image:
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def write_hero_skeleton(style: str, body: Image.Image, *, pad_top: int = 28, pad_bottom: int = 18, pad_side: int = 56) -> None:
    """按全身图尺寸自动生成不裁头的画布与锚点。"""
    bw, bh = body.size
    width = bw + pad_side * 2
    height = bh + pad_top + pad_bottom
    origin_x = width // 2
    origin_y = height - pad_bottom
    pivot_x = bw // 2
    pivot_y = bh - 4
    skel = {
        "width": width,
        "height": height,
        "origin": {"x": origin_x, "y": origin_y},
        "bones": [
            {"name": "root", "parent": None, "x": 0, "y": 0, "rotation": 0, "length": 0, "z": 0},
            {"name": "tail", "parent": "root", "x": -bw * 0.22, "y": -bh * 0.35, "rotation": -12, "length": 40, "z": 5},
            {
                "name": "body",
                "parent": "root",
                "x": 0,
                "y": 0,
                "rotation": 0,
                "length": bh,
                "z": 20,
                "part": "body",
                "pivot_x": pivot_x,
                "pivot_y": pivot_y,
            },
            {"name": "ear_l", "parent": "body", "x": -bw * 0.18, "y": -bh * 0.78, "rotation": -8, "length": 16, "z": 40},
            {"name": "ear_r", "parent": "body", "x": bw * 0.18, "y": -bh * 0.78, "rotation": 8, "length": 16, "z": 40},
            {"name": "torso", "parent": "body", "x": 0, "y": -bh * 0.35, "rotation": 0, "length": 10, "z": 21},
            {"name": "head", "parent": "body", "x": 0, "y": -bh * 0.72, "rotation": 0, "length": 10, "z": 30},
            {"name": "hood", "parent": "head", "x": 0, "y": 0, "rotation": 0, "length": 4, "z": 29},
            {"name": "face", "parent": "head", "x": 0, "y": 8, "rotation": 0, "length": 4, "z": 31},
            {"name": "eyes", "parent": "face", "x": 0, "y": 0, "rotation": 0, "length": 2, "z": 32},
            {"name": "arm_l", "parent": "body", "x": -bw * 0.28, "y": -bh * 0.45, "rotation": 0, "length": 20, "z": 15},
            {"name": "arm_r", "parent": "body", "x": bw * 0.28, "y": -bh * 0.45, "rotation": 0, "length": 20, "z": 15},
            {"name": "leg_l", "parent": "root", "x": -bw * 0.08, "y": -bh * 0.08, "rotation": 0, "length": 20, "z": 10},
            {"name": "leg_r", "parent": "root", "x": bw * 0.08, "y": -bh * 0.08, "rotation": 0, "length": 20, "z": 10},
        ],
    }
    path = CHAR / "variants" / style / "skeleton.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(skel, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  {style} skeleton {width}x{height} (no head crop)")


def build_anime() -> None:
    out = CHAR / "variants" / "anime" / "parts"
    src = RAW / "fullbody.png"
    if not src.exists():
        src = RAW / "fullbody_v1.png"
    full = Image.open(src)
    full = sharpen(trim(remove_bg(full, light_thresh=232, sat_thresh=40)), amount=1.25)

    # 主身体：完整精绘全身（视觉主体）
    body = full.copy()
    target_h = 300
    scale = target_h / body.height
    body = body.resize((max(1, int(body.width * scale)), target_h), Image.Resampling.LANCZOS)
    save_part(body, out, "body")

    # 头切片仅作素材备份
    head = trim(full.crop((0, 0, full.width, int(full.height * 0.48))))
    head = head.resize((int(head.width * (150 / max(1, head.height))), 150), Image.Resampling.LANCZOS)
    save_part(head, out, "head")
    save_part(head.copy(), out, "hood")

    if (RAW / "tail.png").exists():
        tail = sharpen(trim(remove_bg(Image.open(RAW / "tail.png"), light_thresh=230)))
        tail = tail.resize((int(tail.width * (90 / max(1, tail.height))), 90), Image.Resampling.LANCZOS)
        save_part(tail, out, "tail")
    else:
        save_part(make_empty(40, 40), out, "tail")

    save_part(make_empty(8, 8), out, "ear_l")
    save_part(make_empty(8, 8), out, "ear_r")
    save_part(make_empty(8, 8), out, "face")
    save_part(make_empty(8, 8), out, "eyes")
    save_part(make_blush(100, 42), out, "blush")

    torso = trim(full.crop((0, int(full.height * 0.38), full.width, int(full.height * 0.72))))
    torso = torso.resize((120, max(1, int(120 * torso.height / max(1, torso.width)))), Image.Resampling.LANCZOS)
    save_part(torso, out, "torso")

    if (RAW / "arms.png").exists():
        arms = sharpen(trim(remove_bg(Image.open(RAW / "arms.png"), light_thresh=230)))
        left, right = split_lr(arms)
        left = left.resize((36, max(1, int(36 * left.height / max(1, left.width)))), Image.Resampling.LANCZOS)
        right = right.resize((36, max(1, int(36 * right.height / max(1, right.width)))), Image.Resampling.LANCZOS)
        save_part(left, out, "arm_l")
        save_part(right, out, "arm_r")
    else:
        save_part(make_empty(28, 48), out, "arm_l")
        save_part(make_empty(28, 48), out, "arm_r")

    if (RAW / "legs.png").exists():
        legs = sharpen(trim(remove_bg(Image.open(RAW / "legs.png"), light_thresh=230)))
        left, right = split_lr(legs)
        left = left.resize((32, max(1, int(32 * left.height / max(1, left.width)))), Image.Resampling.LANCZOS)
        right = right.resize((32, max(1, int(32 * right.height / max(1, right.width)))), Image.Resampling.LANCZOS)
        save_part(left, out, "leg_l")
        save_part(right, out, "leg_r")
    else:
        legs = trim(full.crop((0, int(full.height * 0.7), full.width, full.height)))
        left, right = split_lr(legs)
        save_part(left.resize((30, 50), Image.Resampling.LANCZOS), out, "leg_l")
        save_part(right.resize((30, 50), Image.Resampling.LANCZOS), out, "leg_r")

    write_hero_skeleton("anime", body)
    legacy = CHAR / "parts"
    legacy.mkdir(exist_ok=True)
    for p in out.glob("*.png"):
        shutil.copy2(p, legacy / p.name)


def build_pixel() -> None:
    out = CHAR / "variants" / "pixel" / "parts"
    src = RAW / "pixel_full.png"
    if not src.exists():
        print("  skip pixel: no raw")
        return
    img = Image.open(src)
    img = trim(remove_bg(img, chroma=(255, 0, 255), light_thresh=245, sat_thresh=40))
    img = trim(remove_bg(img, light_thresh=240, sat_thresh=30))
    target_h = 180
    scale = target_h / max(1, img.height)
    body = img.resize((max(1, int(img.width * scale)), target_h), Image.Resampling.NEAREST)
    save_part(body, out, "body")
    save_part(body.copy(), out, "head")
    save_part(make_empty(), out, "hood")
    save_part(make_empty(), out, "face")
    save_part(make_empty(), out, "eyes")
    save_part(make_blush(60, 28), out, "blush")
    save_part(make_empty(20, 30), out, "torso")
    save_part(make_empty(12, 20), out, "arm_l")
    save_part(make_empty(12, 20), out, "arm_r")
    save_part(make_empty(12, 20), out, "leg_l")
    save_part(make_empty(12, 20), out, "leg_r")
    tw, th = body.size
    tail = trim(body.crop((0, int(th * 0.35), int(tw * 0.35), int(th * 0.85))))
    save_part(tail if tail.getbbox() else make_empty(24, 24), out, "tail")
    ear = trim(body.crop((int(tw * 0.15), 0, int(tw * 0.4), int(th * 0.25))))
    if ear.getbbox():
        save_part(make_empty(8, 8), out, "ear_l")  # 已在 body 上，避免双耳
        save_part(make_empty(8, 8), out, "ear_r")
    else:
        save_part(make_empty(16, 20), out, "ear_l")
        save_part(make_empty(16, 20), out, "ear_r")
    write_hero_skeleton("pixel", body, pad_top=20, pad_bottom=12, pad_side=36)

def patch_animations_for_body() -> None:
    """给关键帧补上 body 骨骼的位移，跟 torso 同步呼吸。"""
    path = CHAR / "animations.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for anim in data.get("animations", {}).values():
        for kf in anim.get("keyframes", []):
            offs = kf.setdefault("offsets", {})
            rots = kf.setdefault("rotations", {})
            if "torso" in offs and "body" not in offs:
                offs["body"] = offs["torso"]
            if "torso" in rots and "body" not in rots:
                rots["body"] = rots["torso"]
            if "head" in rots and "body" in rots:
                # 轻微把头转叠加到 body，增强一体感
                pass
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("  animations patched for body bone")


def main() -> None:
    print("收集 AI 重绘素材…")
    collect_raw()
    print("构建 anime…")
    build_anime()
    print("构建 pixel…")
    build_pixel()
    patch_animations_for_body()
    print("完成。请运行 python main.py 查看。")


if __name__ == "__main__":
    main()
