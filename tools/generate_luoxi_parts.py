"""生成洛茜 Q 版骨骼部件（更清晰的红帽狼耳萌版）。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "characters" / "luoxi" / "parts"


def blank(w: int, h: int) -> Image.Image:
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def save(img: Image.Image, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.png"
    img.save(path)
    print(f"  [OK] {path.name}")


def make_all() -> None:
    # ---- head (脸+头发，不含帽) ----
    img = blank(90, 100)
    d = ImageDraw.Draw(img)
    # 后发
    d.ellipse((8, 28, 82, 96), fill=(196, 52, 58, 255))
    # 脸
    d.ellipse((18, 34, 72, 92), fill=(255, 226, 214, 255))
    # 刘海
    d.pieslice((14, 20, 76, 70), 200, 340, fill=(210, 60, 66, 255))
    d.polygon([(22, 48), (32, 26), (40, 46)], fill=(210, 60, 66, 255))
    d.polygon([(50, 46), (58, 24), (70, 48)], fill=(210, 60, 66, 255))
    # 侧发卷
    d.ellipse((6, 50, 26, 86), fill=(180, 42, 50, 255))
    d.ellipse((64, 50, 84, 86), fill=(180, 42, 50, 255))
    save(img, "head")

    # ---- hood：半透明大帽檐，开口露脸 ----
    img = blank(110, 88)
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, 106, 84), fill=(186, 38, 46, 255))
    # 挖空脸部区域（透明椭圆）
    face_cut = blank(110, 88)
    fd = ImageDraw.Draw(face_cut)
    fd.ellipse((28, 30, 82, 86), fill=(255, 255, 255, 255))
    # 用 alpha 合成挖洞
    base = img
    mask = face_cut.split()[-1]
    # reverse mask: keep hood outside face
    inv = Image.eval(mask, lambda p: 255 - p)
    out = blank(110, 88)
    out.paste(base, (0, 0), inv)
    # 帽内侧一圈浅红描边
    od = ImageDraw.Draw(out)
    od.ellipse((30, 32, 80, 84), outline=(120, 24, 30, 180), width=3)
    # 帽尖小折
    od.polygon([(50, 2), (62, 18), (44, 16)], fill=(160, 30, 38, 255))
    save(out, "hood")

    # ---- wolf ears ----
    for side in ("l", "r"):
        img = blank(34, 46)
        d = ImageDraw.Draw(img)
        if side == "l":
            d.polygon([(17, 1), (1, 42), (26, 38)], fill=(200, 55, 60, 255))
            d.polygon([(17, 10), (8, 36), (22, 34)], fill=(255, 195, 200, 255))
        else:
            d.polygon([(17, 1), (33, 42), (8, 38)], fill=(200, 55, 60, 255))
            d.polygon([(17, 10), (26, 36), (12, 34)], fill=(255, 195, 200, 255))
        save(img, f"ear_{side}")

    # ---- face accents ----
    img = blank(76, 58)
    d = ImageDraw.Draw(img)
    d.ellipse((36, 26, 40, 31), fill=(235, 180, 170, 255))
    d.arc((30, 30, 46, 44), 15, 165, fill=(90, 50, 55, 255), width=2)
    save(img, "face")

    # ---- eyes：偏菱形大眼 ----
    img = blank(64, 28)
    d = ImageDraw.Draw(img)
    for cx in (16, 48):
        d.ellipse((cx - 11, 2, cx + 11, 24), fill=(250, 252, 255, 255), outline=(70, 40, 50, 255))
        d.polygon([(cx, 6), (cx + 6, 14), (cx, 22), (cx - 6, 14)], fill=(130, 195, 235, 255))
        d.ellipse((cx - 2, 11, cx + 2, 17), fill=(35, 45, 65, 255))
        d.ellipse((cx - 4, 7, cx - 1, 10), fill=(255, 255, 255, 230))
    save(img, "eyes")

    # ---- blush ----
    img = blank(76, 36)
    d = ImageDraw.Draw(img)
    d.ellipse((2, 8, 30, 30), fill=(255, 120, 140, 100))
    d.ellipse((46, 8, 74, 30), fill=(255, 120, 140, 100))
    save(img, "blush")

    # ---- torso：白裙+红披风感 ----
    img = blank(88, 100)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((16, 10, 72, 88), radius=22, fill=(248, 240, 232, 255))
    d.rectangle((20, 46, 68, 56), fill=(200, 48, 54, 255))
    # 披风两侧
    d.polygon([(6, 14), (22, 8), (18, 70), (2, 66)], fill=(186, 38, 46, 255))
    d.polygon([(82, 14), (66, 8), (70, 70), (86, 66)], fill=(186, 38, 46, 255))
    d.polygon([(44, 8), (30, 32), (58, 32)], fill=(255, 226, 214, 255))
    # 小装饰扣
    d.ellipse((40, 48, 48, 56), fill=(255, 210, 120, 255))
    save(img, "torso")

    for side in ("l", "r"):
        img = blank(30, 52)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((7, 2, 23, 38), radius=9, fill=(255, 226, 214, 255))
        d.ellipse((5, 34, 25, 50), fill=(255, 226, 214, 255))
        save(img, f"arm_{side}")

        img = blank(26, 52)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((6, 0, 20, 30), radius=7, fill=(248, 240, 232, 255))
        d.rounded_rectangle((4, 28, 22, 50), radius=7, fill=(65, 48, 48, 255))
        save(img, f"leg_{side}")

    # ---- fluffy wolf tail ----
    img = blank(64, 44)
    d = ImageDraw.Draw(img)
    d.ellipse((4, 8, 48, 38), fill=(200, 58, 64, 255))
    d.ellipse((36, 6, 60, 32), fill=(255, 210, 200, 255))
    save(img, "tail")
    print("洛茜部件已更新。")


if __name__ == "__main__":
    make_all()
