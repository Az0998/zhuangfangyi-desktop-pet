"""
main.py — 庄方宜 Q 版桌面宠物 程序入口。

加载配置 → 初始化动画引擎 → 创建宠物窗口 → 系统托盘集成。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)

from pet_animator import PetAnimator
from pet_window import PetWindow


def load_config(path: Path) -> dict:
    """从 JSON 文件加载配置。

    Args:
        path: 配置文件的路径。

    Returns:
        配置字典。
    """
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("庄方宜 Q版桌面宠物")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出，驻留托盘

    # ---- 路径 ----
    base_dir = Path(__file__).resolve().parent
    assets_dir = base_dir / "assets"
    config_path = base_dir / "config.json"

    # ---- 加载配置 ----
    config = load_config(config_path)

    # ---- 动画引擎 ----
    animator = PetAnimator(assets_dir, config)

    # ---- 宠物窗口 ----
    window = PetWindow(animator, config)
    window.show()

    # ---- 系统托盘 ----
    _setup_tray(app, window, assets_dir, config)

    sys.exit(app.exec_())


def _setup_tray(
    app: QApplication,
    window: PetWindow,
    assets_dir: Path,
    config: dict,
) -> None:
    """初始化系统托盘图标和菜单。

    Args:
        app: QApplication 实例。
        window: 宠物窗口。
        assets_dir: 资源目录路径。
        config: 配置字典。
    """
    # 托盘图标——取第一帧或 assets 下的 tray.png
    icon_path = assets_dir / "idle" / "frame_01.png"
    icon = QIcon()
    if icon_path.exists():
        icon = QIcon(str(icon_path))
    else:
        # 程序图标兜底
        pix = QPixmap(64, 64)
        pix.fill(Qt.GlobalColor.transparent)
        icon = QIcon(pix)

    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("庄方宜 Q版桌面宠物")

    menu = QMenu()

    show_action = menu.addAction("显示/隐藏")
    show_action.triggered.connect(lambda: _toggle_window(window))

    menu.addSeparator()

    action_menu = menu.addMenu("切换动作")
    action_names = list(config["animation"]["actions"].keys())
    for name in action_names:
        act = action_menu.addAction(name)
        act.triggered.connect(lambda checked=False, n=name: window._switch_action(n))

    menu.addSeparator()

    about_action = menu.addAction("关于")
    about_action.triggered.connect(window._show_about)

    exit_action = menu.addAction("退出")
    exit_action.triggered.connect(lambda: _quit_app(app, tray))

    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: _toggle_window(window) if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None
    )
    tray.show()


def _toggle_window(window: PetWindow) -> None:
    """显示/隐藏宠物窗口。"""
    if window.isVisible():
        window.hide()
    else:
        window.show()
        window.raise_()
        window.activateWindow()


def _quit_app(app: QApplication, tray: QSystemTrayIcon) -> None:
    """完全退出应用（移除托盘图标后退出）。"""
    tray.hide()
    app.quit()


if __name__ == "__main__":
    main()
