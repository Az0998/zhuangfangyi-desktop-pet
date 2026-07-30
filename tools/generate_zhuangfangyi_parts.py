"""生成庄方宜 Q 版骨骼部件。运行: python tools/generate_zhuangfangyi_parts.py"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "characters" / "zhuangfangyi" / "parts"

C = {
    "skin": (255, 224, 210, 255),
    "hair": (28, 28, 32, 255),
    "robe": (45, 90, 39, 255),
    "trim": (212, 175, 122, 255),
    "horn": (139, 111, 71, 255),
    "eye_white": (245, 250, 255, 255),
    "iris": (180, 220, 160, 255),
    "pupil": (30, 40, 30, 255),
    "blush": (255, 140, 140, 70),
    "boot": (50, 40, 35, 255),
    "line": (40, 50, 35, 255),
}


def blank(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def save(img, name):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{name}.png"
    img.save(p)
    print(f"  [OK] {p}")


def main():
    # head
    img = blank(84, 96)
    d = ImageDraw.Draw(img)
    d.ellipse((10, 20, 74, 90), fill=C["hair"])
    d.ellipse((18, 30, 66, 84), fill=C["skin"])
    d.polygon([(20, 38), (32, 16), (42, 34), (52, 14), (66, 38), (58, 46), (26, 46)], fill=C["hair"])
    save(img, "head")

    # hood unused -> simple hair ornament as hood layer (transparent-ish cape clip)
    img = blank(96, 80)
    d = ImageDraw.Draw(img)
    d.ellipse((28, 8, 44, 28), fill=C["horn"])  # left horn marker on layer
    d.ellipse((52, 8, 68, 28), fill=C["horn"])
    save(img, "hood")

    for side in ("l", "r"):
        img = blank(28, 40)
        d = ImageDraw.Draw(img)
        # reuse ear slots as kirin horns
        if side == "l":
            d.polygon([(14, 2), (4, 34), (20, 30)], fill=C["horn"])
        else:
            d.polygon([(14, 2), (24, 34), (8, 30)], fill=C["horn"])
        save(img, f"ear_{side}")

    img = blank(72, 56)
    d = ImageDraw.Draw(img)
    d.ellipse((34, 28, 38, 32), fill=(230, 190, 175, 255))
    d.arc((30, 32, 42, 42), 20, 160, fill=C["line"], width=2)
    save(img, "face")

    img = blank(56, 24)
    d = ImageDraw.Draw(img)
    for cx in (14, 42):
        d.ellipse((cx - 9, 2, cx + 9, 20), fill=C["eye_white"], outline=C["line"])
        d.ellipse((cx - 4, 6, cx + 4, 16), fill=C["iris"])
        d.ellipse((cx - 2, 8, cx + 2, 14), fill=C["pupil"])
    save(img, "eyes")

    img = blank(72, 40)
    d = ImageDraw.Draw(img)
    d.ellipse((6, 12, 26, 28), fill=C["blush"])
    d.ellipse((46, 12, 66, 28), fill=C["blush"])
    save(img, "blush")

    img = blank(80, 90)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((14, 8, 66, 80), radius=16, fill=C["robe"])
    d.rectangle((18, 42, 62, 50), fill=C["trim"])
    d.polygon([(40, 8), (28, 26), (52, 26)], fill=C["skin"])
    save(img, "torso")

    for side in ("l", "r"):
        img = blank(28, 48)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((6, 2, 22, 40), radius=8, fill=C["skin"])
        save(img, f"arm_{side}")
        img = blank(24, 48)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((6, 0, 18, 28), radius=6, fill=C["robe"])
        d.rounded_rectangle((4, 26, 20, 46), radius=6, fill=C["boot"])
        save(img, f"leg_{side}")

    img = blank(56, 40)
    d = ImageDraw.Draw(img)
    # small sash / no wolf tail — decorative ribbon
    d.polygon([(8, 12), (40, 4), (48, 16), (30, 28), (10, 22)], fill=C["trim"])
    save(img, "tail")
    print("庄方宜部件完成。")


if __name__ == "__main__":
    main()
