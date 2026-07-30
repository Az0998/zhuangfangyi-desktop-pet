"""
终末地桌宠 — 程序入口。

双画风分层立绘 · 骨骼动作链 · AI 对话 · 剪贴板 · 日程提醒
默认角色：洛茜（洛希）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from core.character import list_characters, load_character
from core.skeletal_animator import SkeletalAnimator
from ui.pet_window import PetWindow


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("终末地桌宠")
    app.setQuitOnLastWindowClosed(False)

    base_dir = Path(__file__).resolve().parent
    config = load_config(base_dir / "config.json")

    character_id = config.get("character_id", "luoxi")
    art_style = config.get("art_style", "anime")
    try:
        character = load_character(character_id, base_dir, art_style=art_style)
    except FileNotFoundError:
        available = list_characters(base_dir)
        if not available:
            raise SystemExit("未找到任何角色包，请检查 characters/ 目录。")
        character = load_character(available[0]["id"], base_dir, art_style=art_style)

    tick_ms = int(config.get("animation", {}).get("tick_ms", 33))
    animator = SkeletalAnimator(character, tick_ms=tick_ms)
    window = PetWindow(animator, character, config, base_dir)
    window.show()

    _setup_tray(app, window, character, base_dir)
    sys.exit(app.exec_())


def _setup_tray(app: QApplication, window: PetWindow, character, base_dir: Path) -> None:
    icon_path = character.parts_dir / "head.png"
    if icon_path.exists():
        icon = QIcon(str(icon_path))
    else:
        pix = QPixmap(64, 64)
        pix.fill(Qt.GlobalColor.transparent)
        icon = QIcon(pix)

    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip(f"{character.name} · 终末地桌宠")

    def rebuild_menu() -> None:
        menu = QMenu()
        menu.addAction("显示/隐藏").triggered.connect(lambda: _toggle(window))
        menu.addAction("和她聊天…").triggered.connect(window.open_chat)
        menu.addAction("剪贴板历史…").triggered.connect(window.open_clipboard)
        menu.addAction("日程 / 健康提醒…").triggered.connect(window.open_schedule)
        menu.addSeparator()

        styles = menu.addMenu("画风")
        for style in window._character.variants:
            label = {"anime": "动漫版", "pixel": "像素版"}.get(style, style)
            styles.addAction(label).triggered.connect(
                lambda checked=False, s=style: window.set_art_style(s)
            )

        chars = menu.addMenu("更换角色")
        for info in list_characters(base_dir):
            chars.addAction(info["name"]).triggered.connect(
                lambda checked=False, cid=info["id"]: window._switch_character(cid)
            )

        menu.addSeparator()
        menu.addAction("关于").triggered.connect(window._show_about)
        menu.addAction("退出").triggered.connect(lambda: _quit(app, tray))
        tray.setContextMenu(menu)
        tray.setToolTip(f"{window._character.name} · {window._character.art_style}")
        head = window._character.parts_dir / "head.png"
        if head.exists():
            tray.setIcon(QIcon(str(head)))

    rebuild_menu()
    window.character_changed.connect(lambda _cid: rebuild_menu())
    tray.activated.connect(
        lambda reason: _toggle(window)
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick
        else None
    )
    tray.show()


def _toggle(window: PetWindow) -> None:
    if window.isVisible():
        window.hide()
    else:
        window.show()
        window.raise_()


def _quit(app: QApplication, tray: QSystemTrayIcon) -> None:
    tray.hide()
    app.quit()


if __name__ == "__main__":
    main()
