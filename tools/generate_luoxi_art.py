"""生成洛茜分层立绘：anime（赛璐璐）与 pixel（点阵）两套。

部件命名与 skeleton 中 part 字段对齐，可替换为真实绘制的 PNG。
运行：python tools/generate_luoxi_art.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent / "characters" / "luoxi" / "variants"


def blank(w: int, h: int) -> Image.Image:
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def save(img: Image.Image, folder: Path, name: str, pixel: bool = False) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    if pixel:
        # 保持锐利像素边缘
        img = img.resize(img.size, Image.Resampling.NEAREST)
    img.save(folder / f"{name}.png")


# ---------------------------------------------------------------------------
# Anime (higher-res soft shading)
# ---------------------------------------------------------------------------

def anime_parts() -> None:
    out = ROOT / "anime" / "parts"

    # head
    img = blank(120, 130)
    d = ImageDraw.Draw(img)
    d.ellipse((12, 34, 108, 126), fill=(198, 48, 56, 255))  # back hair
    d.ellipse((24, 42, 96, 118), fill=(255, 228, 216, 255))  # face
    # bangs
    d.pieslice((18, 24, 102, 90), 200, 340, fill=(214, 58, 66, 255))
    d.polygon([(28, 60), (40, 30), (50, 58)], fill=(214, 58, 66, 255))
    d.polygon([(70, 58), (80, 28), (94, 60)], fill=(214, 58, 66, 255))
    d.ellipse((8, 62, 34, 110), fill=(176, 40, 48, 255))
    d.ellipse((86, 62, 112, 110), fill=(176, 40, 48, 255))
    # soft shade
    shade = blank(120, 130)
    sd = ImageDraw.Draw(shade)
    sd.ellipse((30, 80, 90, 118), fill=(240, 190, 180, 70))
    img = Image.alpha_composite(img, shade)
    save(img, out, "head")

    # hood with face cutout
    img = blank(140, 110)
    d = ImageDraw.Draw(img)
    d.ellipse((6, 6, 134, 104), fill=(186, 36, 46, 255))
    cut = blank(140, 110)
    ImageDraw.Draw(cut).ellipse((36, 38, 104, 108), fill=(255, 255, 255, 255))
    inv = Image.eval(cut.split()[-1], lambda p: 255 - p)
    hood = blank(140, 110)
    hood.paste(img, (0, 0), inv)
    hd = ImageDraw.Draw(hood)
    hd.ellipse((38, 40, 102, 106), outline=(110, 22, 28, 200), width=3)
    hd.polygon([(64, 2), (78, 22), (56, 20)], fill=(150, 28, 36, 255))
    # rim highlight
    hd.arc((12, 10, 128, 70), 210, 330, fill=(255, 170, 170, 160), width=3)
    save(hood, out, "hood")

    for side in ("l", "r"):
        img = blank(42, 56)
        d = ImageDraw.Draw(img)
        if side == "l":
            d.polygon([(21, 2), (2, 52), (32, 46)], fill=(205, 52, 60, 255))
            d.polygon([(21, 12), (10, 44), (28, 40)], fill=(255, 198, 204, 255))
        else:
            d.polygon([(21, 2), (40, 52), (10, 46)], fill=(205, 52, 60, 255))
            d.polygon([(21, 12), (32, 44), (14, 40)], fill=(255, 198, 204, 255))
        save(img, out, f"ear_{side}")

    img = blank(96, 70)
    d = ImageDraw.Draw(img)
    d.ellipse((46, 32, 50, 37), fill=(235, 185, 175, 255))
    d.arc((38, 36, 58, 54), 20, 160, fill=(95, 55, 60, 255), width=2)
    save(img, out, "face")

    img = blank(84, 34)
    d = ImageDraw.Draw(img)
    for cx in (20, 64):
        d.ellipse((cx - 14, 2, cx + 14, 30), fill=(252, 254, 255, 255), outline=(70, 42, 52, 255), width=2)
        d.polygon([(cx, 6), (cx + 8, 17), (cx, 28), (cx - 8, 17)], fill=(120, 190, 235, 255))
        d.ellipse((cx - 3, 14, cx + 3, 22), fill=(32, 42, 62, 255))
        d.ellipse((cx - 6, 8, cx - 2, 12), fill=(255, 255, 255, 240))
    save(img, out, "eyes")

    img = blank(96, 42)
    d = ImageDraw.Draw(img)
    d.ellipse((4, 10, 36, 36), fill=(255, 120, 145, 110))
    d.ellipse((60, 10, 92, 36), fill=(255, 120, 145, 110))
    save(img, out, "blush")

    img = blank(110, 120)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 12, 90, 108), radius=26, fill=(250, 243, 236, 255))
    d.rectangle((24, 54, 86, 66), fill=(200, 46, 54, 255))
    d.polygon([(8, 16), (28, 10), (24, 86), (4, 80)], fill=(186, 36, 46, 255))
    d.polygon([(102, 16), (82, 10), (86, 86), (106, 80)], fill=(186, 36, 46, 255))
    d.polygon([(55, 10), (38, 38), (72, 38)], fill=(255, 228, 216, 255))
    d.ellipse((50, 56, 60, 66), fill=(255, 214, 130, 255))
    # cloth shade
    shade = blank(110, 120)
    ImageDraw.Draw(shade).rounded_rectangle((24, 70, 86, 106), radius=18, fill=(230, 210, 200, 60))
    img = Image.alpha_composite(img, shade)
    save(img, out, "torso")

    for side in ("l", "r"):
        img = blank(36, 64)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((8, 2, 28, 46), radius=11, fill=(255, 228, 216, 255))
        d.ellipse((6, 42, 30, 62), fill=(255, 228, 216, 255))
        save(img, out, f"arm_{side}")
        img = blank(30, 64)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((6, 0, 24, 36), radius=8, fill=(250, 243, 236, 255))
        d.rounded_rectangle((4, 34, 26, 62), radius=8, fill=(68, 48, 48, 255))
        save(img, out, f"leg_{side}")

    img = blank(78, 52)
    d = ImageDraw.Draw(img)
    d.ellipse((4, 10, 58, 44), fill=(205, 55, 62, 255))
    d.ellipse((44, 6, 74, 38), fill=(255, 214, 205, 255))
    fluffy = img.filter(ImageFilter.GaussianBlur(0.4))
    save(fluffy, out, "tail")
    print("  anime parts OK")


# ---------------------------------------------------------------------------
# Pixel (nearest, limited palette, chunky)
# ---------------------------------------------------------------------------

def _px(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, color) -> None:
    draw.rectangle((x, y, x + w - 1, y + h - 1), fill=color)


def pixel_parts() -> None:
    out = ROOT / "pixel" / "parts"
    # work at 2x then downscale with NEAREST for crisp pixels? Or draw at final size.
    scale = 4  # draw logical pixels as 4x4 blocks on larger canvas then leave as-is for skeleton

    def canvas(lw: int, lh: int) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
        img = blank(lw * scale, lh * scale)
        return img, ImageDraw.Draw(img), scale

    def p(d, s, x, y, w, h, c):
        _px(d, x * s, y * s, w * s, h * s, c)

    RED = (196, 48, 56, 255)
    RED2 = (160, 32, 40, 255)
    PINK = (255, 190, 198, 255)
    SKIN = (255, 220, 205, 255)
    WHITE = (250, 245, 240, 255)
    BOOT = (60, 44, 44, 255)
    EYE = (110, 185, 230, 255)
    DARK = (40, 40, 55, 255)
    GOLD = (255, 210, 120, 255)
    BLUSH = (255, 120, 140, 140)

    # head 28x32 logical
    img, d, s = canvas(28, 32)
    p(d, s, 4, 10, 20, 18, RED)
    p(d, s, 6, 12, 16, 16, SKIN)
    p(d, s, 5, 8, 18, 8, RED)
    p(d, s, 2, 14, 5, 12, RED2)
    p(d, s, 21, 14, 5, 12, RED2)
    save(img, out, "head", pixel=True)

    img, d, s = canvas(34, 26)
    # hood with face hole via mask
    base = blank(34 * s, 26 * s)
    bd = ImageDraw.Draw(base)
    p(bd, s, 1, 2, 32, 22, RED)
    p(bd, s, 14, 0, 6, 4, RED2)
    mask = blank(34 * s, 26 * s)
    md = ImageDraw.Draw(mask)
    # opaque where hood keeps
    p(md, s, 1, 2, 32, 22, (255, 255, 255, 255))
    # punch face hole
    for yy in range(10, 24):
        for xx in range(9, 25):
            _px(md, xx * s, yy * s, s, s, (0, 0, 0, 0))
    hood = blank(34 * s, 26 * s)
    hood.paste(base, (0, 0), mask.split()[-1])
    save(hood, out, "hood", pixel=True)

    for side in ("l", "r"):
        img, d, s = canvas(10, 14)
        if side == "l":
            p(d, s, 3, 0, 5, 12, RED)
            p(d, s, 4, 3, 3, 7, PINK)
        else:
            p(d, s, 2, 0, 5, 12, RED)
            p(d, s, 3, 3, 3, 7, PINK)
        save(img, out, f"ear_{side}", pixel=True)

    img, d, s = canvas(22, 16)
    p(d, s, 10, 8, 2, 2, (230, 180, 170, 255))
    p(d, s, 8, 11, 6, 1, DARK)
    save(img, out, "face", pixel=True)

    img, d, s = canvas(20, 8)
    for cx in (4, 14):
        p(d, s, cx, 1, 5, 5, WHITE)
        p(d, s, cx + 1, 2, 3, 3, EYE)
        p(d, s, cx + 2, 3, 1, 2, DARK)
    save(img, out, "eyes", pixel=True)

    img, d, s = canvas(22, 10)
    p(d, s, 1, 3, 6, 4, BLUSH)
    p(d, s, 15, 3, 6, 4, BLUSH)
    save(img, out, "blush", pixel=True)

    img, d, s = canvas(26, 28)
    p(d, s, 5, 2, 16, 22, WHITE)
    p(d, s, 5, 12, 16, 3, RED)
    p(d, s, 0, 3, 6, 16, RED)
    p(d, s, 20, 3, 6, 16, RED)
    p(d, s, 9, 2, 8, 6, SKIN)
    p(d, s, 11, 13, 4, 3, GOLD)
    save(img, out, "torso", pixel=True)

    for side in ("l", "r"):
        img, d, s = canvas(8, 14)
        p(d, s, 2, 0, 4, 10, SKIN)
        p(d, s, 1, 9, 6, 4, SKIN)
        save(img, out, f"arm_{side}", pixel=True)
        img, d, s = canvas(7, 14)
        p(d, s, 1, 0, 5, 8, WHITE)
        p(d, s, 1, 8, 5, 6, BOOT)
        save(img, out, f"leg_{side}", pixel=True)

    img, d, s = canvas(18, 12)
    p(d, s, 1, 3, 12, 7, RED)
    p(d, s, 10, 2, 7, 6, PINK)
    save(img, out, "tail", pixel=True)
    print("  pixel parts OK")


def write_skeletons() -> None:
    anime_skel = {
        "width": 240,
        "height": 300,
        "origin": {"x": 120, "y": 230},
        "bones": [
            {"name": "root", "parent": None, "x": 0, "y": 0, "rotation": 0, "length": 0, "z": 0},
            {"name": "torso", "parent": "root", "x": 0, "y": -48, "rotation": 0, "length": 48, "z": 20,
             "part": "torso", "pivot_x": 55, "pivot_y": 70},
            {"name": "tail", "parent": "torso", "x": -26, "y": 26, "rotation": -22, "length": 42, "z": 8,
             "part": "tail", "pivot_x": 12, "pivot_y": 24},
            {"name": "arm_l", "parent": "torso", "x": -40, "y": -22, "rotation": 14, "length": 34, "z": 12,
             "part": "arm_l", "pivot_x": 18, "pivot_y": 6},
            {"name": "arm_r", "parent": "torso", "x": 40, "y": -22, "rotation": -14, "length": 34, "z": 28,
             "part": "arm_r", "pivot_x": 18, "pivot_y": 6},
            {"name": "leg_l", "parent": "root", "x": -16, "y": -4, "rotation": 5, "length": 40, "z": 10,
             "part": "leg_l", "pivot_x": 15, "pivot_y": 2},
            {"name": "leg_r", "parent": "root", "x": 16, "y": -4, "rotation": -5, "length": 40, "z": 10,
             "part": "leg_r", "pivot_x": 15, "pivot_y": 2},
            {"name": "head", "parent": "torso", "x": 0, "y": -66, "rotation": 0, "length": 34, "z": 40,
             "part": "head", "pivot_x": 60, "pivot_y": 88},
            {"name": "hood", "parent": "head", "x": 0, "y": -20, "rotation": 0, "length": 14, "z": 35,
             "part": "hood", "pivot_x": 70, "pivot_y": 70},
            {"name": "ear_l", "parent": "head", "x": -30, "y": -40, "rotation": -16, "length": 22, "z": 55,
             "part": "ear_l", "pivot_x": 21, "pivot_y": 48},
            {"name": "ear_r", "parent": "head", "x": 30, "y": -40, "rotation": 16, "length": 22, "z": 55,
             "part": "ear_r", "pivot_x": 21, "pivot_y": 48},
            {"name": "face", "parent": "head", "x": 0, "y": 4, "rotation": 0, "length": 8, "z": 50,
             "part": "face", "pivot_x": 48, "pivot_y": 36},
            {"name": "eyes", "parent": "face", "x": 0, "y": -10, "rotation": 0, "length": 4, "z": 60,
             "part": "eyes", "pivot_x": 42, "pivot_y": 16},
        ],
    }
    pixel_skel = {
        "width": 160,
        "height": 200,
        "origin": {"x": 80, "y": 155},
        "bones": [
            {"name": "root", "parent": None, "x": 0, "y": 0, "rotation": 0, "length": 0, "z": 0},
            {"name": "torso", "parent": "root", "x": 0, "y": -36, "rotation": 0, "length": 36, "z": 20,
             "part": "torso", "pivot_x": 52, "pivot_y": 56},
            {"name": "tail", "parent": "torso", "x": -20, "y": 18, "rotation": -20, "length": 28, "z": 8,
             "part": "tail", "pivot_x": 8, "pivot_y": 20},
            {"name": "arm_l", "parent": "torso", "x": -28, "y": -14, "rotation": 12, "length": 24, "z": 12,
             "part": "arm_l", "pivot_x": 16, "pivot_y": 4},
            {"name": "arm_r", "parent": "torso", "x": 28, "y": -14, "rotation": -12, "length": 24, "z": 28,
             "part": "arm_r", "pivot_x": 16, "pivot_y": 4},
            {"name": "leg_l", "parent": "root", "x": -12, "y": -2, "rotation": 5, "length": 28, "z": 10,
             "part": "leg_l", "pivot_x": 14, "pivot_y": 2},
            {"name": "leg_r", "parent": "root", "x": 12, "y": -2, "rotation": -5, "length": 28, "z": 10,
             "part": "leg_r", "pivot_x": 14, "pivot_y": 2},
            {"name": "head", "parent": "torso", "x": 0, "y": -48, "rotation": 0, "length": 24, "z": 40,
             "part": "head", "pivot_x": 56, "pivot_y": 88},
            {"name": "hood", "parent": "head", "x": 0, "y": -14, "rotation": 0, "length": 10, "z": 35,
             "part": "hood", "pivot_x": 68, "pivot_y": 70},
            {"name": "ear_l", "parent": "head", "x": -22, "y": -30, "rotation": -14, "length": 16, "z": 55,
             "part": "ear_l", "pivot_x": 20, "pivot_y": 48},
            {"name": "ear_r", "parent": "head", "x": 22, "y": -30, "rotation": 14, "length": 16, "z": 55,
             "part": "ear_r", "pivot_x": 20, "pivot_y": 48},
            {"name": "face", "parent": "head", "x": 0, "y": 2, "rotation": 0, "length": 6, "z": 50,
             "part": "face", "pivot_x": 44, "pivot_y": 36},
            {"name": "eyes", "parent": "face", "x": 0, "y": -6, "rotation": 0, "length": 3, "z": 60,
             "part": "eyes", "pivot_x": 40, "pivot_y": 16},
        ],
    }
    import json

    for style, data in (("anime", anime_skel), ("pixel", pixel_skel)):
        path = ROOT / style / "skeleton.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {style} skeleton OK")


def main() -> None:
    print("生成洛茜双画风分层立绘…")
    anime_parts()
    pixel_parts()
    write_skeletons()
    # 兼容：把 anime 同步到旧 parts/
    legacy = Path(__file__).resolve().parent.parent / "characters" / "luoxi" / "parts"
    anime_dir = ROOT / "anime" / "parts"
    legacy.mkdir(parents=True, exist_ok=True)
    for p in anime_dir.glob("*.png"):
        (legacy / p.name).write_bytes(p.read_bytes())
    print("完成。可用真实 PNG 替换 variants/<style>/parts/ 下同名文件。")


if __name__ == "__main__":
    main()
