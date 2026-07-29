"""
generate_placeholders.py — 为各个动作生成简易占位 PNG 序列帧。

使用纯 Python 标准库（struct + zlib）创建小尺寸透明背景 PNG，
每个动作画一个带颜色的 Q 版二头身简笔小人 + 动作名称文字。

依赖：无（仅 Python 标准库）
运行：python generate_placeholders.py
"""

import struct
import zlib
import pathlib

BASE = pathlib.Path(__file__).resolve().parent / "assets"

# 每个动作的配色（主色、辅色）和帧数
ACTIONS = {
    "idle":   {"frames": 4, "color": (0x2d, 0x5a, 0x27), "label": "站立"},
    "walk":   {"frames": 4, "color": (0x3a, 0x6b, 0x8f), "label": "行走"},
    "wave":   {"frames": 3, "color": (0x8f, 0x5a, 0x3a), "label": "挥手"},
    "happy":  {"frames": 3, "color": (0x7a, 0x8c, 0x2d), "label": "开心"},
    "sleepy": {"frames": 3, "color": (0x5a, 0x4a, 0x6a), "label": "瞌睡"},
}

WIDTH, HEIGHT = 120, 160


def make_png(width: int, height: int, pixels: bytes) -> bytes:
    """从 RGBA 像素数据构建 PNG 文件字节。"""
    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    # IHDR
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    # 8-bit RGBA (color type 6)

    # IDAT — raw 数据: 每行以 filter byte 0 开头
    raw = b""
    for y in range(height):
        raw += b"\x00" + pixels[y * width * 4 : (y + 1) * width * 4]
    compressed = zlib.compress(raw)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr_data)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )


def make_placeholder_pixels(
    width: int,
    height: int,
    main_color: tuple,
    frame_index: int,
    total_frames: int,
    label: str,
) -> bytes:
    """绘制一个简单的二头身小人占位图。"""
    pixels = bytearray(width * height * 4)  # RGBA, initially transparent

    r, g, b = main_color
    # 根据帧号微小偏移，模拟动画变化
    offset = frame_index * 3

    # ---- 画身体（圆角矩形，二头身） ----
    # 头: 中心 (cx, head_top), 半径 ~20
    cx = width // 2
    head_cy = 38
    head_r = 20
    # 身体: 矩形区域
    body_left = cx - 18
    body_right = cx + 18
    body_top = head_cy + head_r - 6 + offset % 4
    body_bottom = height - 30

    def put_pixel(px, py, pr, pg, pb, pa=255):
        if 0 <= px < width and 0 <= py < height:
            idx = (py * width + px) * 4
            pixels[idx] = pr
            pixels[idx + 1] = pg
            pixels[idx + 2] = pb
            pixels[idx + 3] = pa

    def fill_rect(x1, y1, x2, y2, pr, pg, pb):
        for y in range(max(0, y1), min(height, y2 + 1)):
            for x in range(max(0, x1), min(width, x2 + 1)):
                put_pixel(x, y, pr, pg, pb)

    def fill_circle(cx_, cy_, r_, pr, pg, pb):
        for dy in range(-r_, r_ + 1):
            for dx in range(-r_, r_ + 1):
                if dx * dx + dy * dy <= r_ * r_:
                    put_pixel(cx_ + dx, cy_ + dy, pr, pg, pb)

    # 画头部（圆形）
    fill_circle(cx, head_cy, head_r, r, g, b)

    # 麒麟角（两个小角）
    horn_color = (0x8B, 0x6F, 0x47)
    for side in (-1, 1):
        hx = cx + side * 10
        hy = head_cy - head_r - 4 - offset % 3
        fill_circle(hx, hy, 5, *horn_color)
        fill_circle(hx, hy - 4, 3, *horn_color)

    # 眼睛
    eye_color = (0xFF, 0xFF, 0xFF)
    pupil_color = (0x00, 0x00, 0x00)
    eye_y = head_cy - 2
    for side in (-1, 1):
        ex = cx + side * 8
        fill_circle(ex, eye_y, 4, *eye_color)
        fill_circle(ex, eye_y, 2, *pupil_color)

    # 身体（矩形）
    fill_rect(body_left, body_top, body_right, body_bottom, r, g, b)

    # 传统服饰领口（浅色 V 形）
    fill_rect(body_left + 4, body_top, body_right - 4, body_top + 4, 0xD4, 0xAF, 0x7A)

    # 手臂（根据动作变化）
    arm_color = (r - 20, g - 10, b - 10)
    # 左手
    arm_y = body_top + 8
    if label == "挥手":
        # 抬起手臂
        arm_x1 = body_right + 2
        arm_x2 = body_right + 16 + offset % 6
        fill_rect(arm_x1, arm_y - 6, arm_x2, arm_y + 4, *arm_color)
    else:
        fill_rect(body_right + 2, arm_y, body_right + 12, arm_y + 18, *arm_color)
    # 右手
    fill_rect(body_left - 12, arm_y, body_left - 2, arm_y + 18, *arm_color)

    # 腿部（简单两条线）
    leg_color = (r - 30, g - 20, b - 20)
    leg_y1 = body_bottom
    leg_y2 = height - 12
    step_offset = (offset % 8) - 4 if label == "行走" else 0
    fill_rect(cx - 10 + step_offset, leg_y1, cx - 2, leg_y2, *leg_color)
    fill_rect(cx + 2 - step_offset, leg_y1, cx + 10, leg_y2, *leg_color)

    return bytes(pixels)


def main():
    for action_name, info in ACTIONS.items():
        action_dir = BASE / action_name
        action_dir.mkdir(parents=True, exist_ok=True)

        for i in range(1, info["frames"] + 1):
            pixels = make_placeholder_pixels(
                WIDTH, HEIGHT, info["color"], i - 1, info["frames"], info["label"]
            )
            png_data = make_png(WIDTH, HEIGHT, pixels)
            filepath = action_dir / f"frame_{i:02d}.png"
            filepath.write_bytes(png_data)
            print(f"  [OK] {filepath}")

    print("占位图片生成完毕。")


if __name__ == "__main__":
    main()
