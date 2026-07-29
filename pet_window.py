"""
pet_window.py — 宠物窗口类。

无边框、透明背景、置顶显示的浮动窗口，处理鼠标交互（拖拽、点击、右键菜单）
以及语音气泡和空闲状态切换。
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path

from PyQt5.QtCore import QPoint, Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QCursor, QMouseEvent, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QLabel,
    QMenu,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from pet_animator import PetAnimator


class BubbleWidget(QWidget):
    """语音气泡子窗口。

    半透明圆角矩形背景，3 秒后自动关闭。
    """

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # 文字标签
        self._label = QLabel(text, self)
        self._label.setStyleSheet(
            "background-color: rgba(255, 255, 255, 200);"
            "color: #2d2d2d;"
            "border-radius: 8px;"
            "padding: 8px 14px;"
            "font-size: 14px;"
            "font-family: 'Microsoft YaHei', 'SimHei', sans-serif;"
        )
        self._label.adjustSize()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self.setLayout(layout)

        # 调整气泡尺寸
        self.resize(self._label.sizeHint().width() + 20, self._label.sizeHint().height() + 12)

        # 3 秒后自动关闭
        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self.close)
        self._close_timer.start(3000)

    def position_above(self, widget: QWidget, offset_y: int = 10) -> None:
        """将气泡定位在 *widget* 正上方。"""
        parent_pos = widget.mapToGlobal(QPoint(0, 0))
        bubble_x = parent_pos.x() + (widget.width() - self.width()) // 2
        bubble_y = parent_pos.y() - self.height() - offset_y
        self.move(bubble_x, bubble_y)


class PetWindow(QWidget):
    """宠物主窗口。

    无边框、透明背景、始终置顶。显示动画帧，处理鼠标交互和状态切换。
    """

    def __init__(self, animator: PetAnimator, config: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._animator = animator
        self._config = config
        self._bubble_lines: list[str] = config["bubble"]["lines"]
        self._idle_timeout: int = config["animation"]["idle_timeout_ms"]
        self._mouse_proximity_px: int = config.get("mouse_proximity_px", 80)

        self._drag_offset = QPoint()
        self._dragging: bool = False
        self._last_activity_time: float = time.monotonic()

        # 当前气泡（同一时间只显示一个）
        self._current_bubble: BubbleWidget | None = None

        # ---------- 窗口属性 ----------
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # ---------- 图片显示 ----------
        self._image_label = QLabel(self)
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._image_label)
        self.setLayout(layout)

        # 默认窗口尺寸
        cfg_win = config.get("window", {})
        self.resize(
            cfg_win.get("default_width", 180),
            cfg_win.get("default_height", 240),
        )
        self.move(
            cfg_win.get("default_x", 300),
            cfg_win.get("default_y", 300),
        )

        # ---------- 动画信号连接 ----------
        self._animator.frame_changed.connect(self._on_frame_changed)

        # ---------- 空闲状态定时器 ----------
        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._check_idle)
        self._idle_timer.start(2000)  # 每 2 秒检查一次

        # 初始播放空闲动作
        self._animator.play(self._animator.get_idle_action())

    # ------------------------------------------------------------------
    # 动画帧更新
    # ------------------------------------------------------------------

    @pyqtSlot(QPixmap)
    def _on_frame_changed(self, pixmap: QPixmap) -> None:
        """接收动画引擎发出的帧并显示。"""
        self._image_label.setPixmap(pixmap)
        self._image_label.resize(pixmap.size())
        self.resize(pixmap.size())

    # ------------------------------------------------------------------
    # 鼠标交互
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        """记录拖拽起始点。"""
        if event is None:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            self._dragging = False
            self._reset_idle_timer()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        """按住左键时拖拽窗口。"""
        if event is None:
            return
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPos() - self._drag_offset)
            self._dragging = True
            self._reset_idle_timer()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        """松开左键：若没有拖拽则触发点击交互。"""
        if event is None:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._dragging:
                self._on_click()
            self._dragging = False
            self._reset_idle_timer()
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        """右键弹出菜单。"""
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #f5f5f5; border: 1px solid #aaa; border-radius: 4px; }"
            "QMenu::item { padding: 6px 20px; }"
            "QMenu::item:selected { background: #4a86c8; color: white; }"
        )

        # 切换动作子菜单
        action_menu = menu.addMenu("切换动作")
        action_names = list(self._config["animation"]["actions"].keys())
        for name in action_names:
            act = action_menu.addAction(name)
            act.triggered.connect(lambda checked=False, n=name: self._switch_action(n))

        menu.addSeparator()

        about_action = menu.addAction("关于")
        about_action.triggered.connect(self._show_about)

        menu.addSeparator()

        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(self._exit_app)

        menu.exec_(event.globalPos())
        self._reset_idle_timer()

    # ------------------------------------------------------------------
    # 点击交互（挥手 + 气泡）
    # ------------------------------------------------------------------

    def _on_click(self) -> None:
        """点击时：触发挥手动作 + 弹出随机语音气泡。"""
        # 播放一次挥手（完成后回到空闲）
        self._animator.play("wave")
        # 挥手动画完成后切回空闲
        QTimer.singleShot(
            self._config["animation"]["frame_interval_ms"] * 3 + 100,
            lambda: self._animator.play(self._animator.get_idle_action()),
        )
        self._show_bubble()

    def _show_bubble(self) -> None:
        """在宠物头顶显示随机台词语音气泡。"""
        # 关闭已有气泡
        if self._current_bubble is not None:
            self._current_bubble.close()

        text = random.choice(self._bubble_lines)
        bubble = BubbleWidget(text, self)
        bubble.position_above(self)
        bubble.show()
        self._current_bubble = bubble

    # ------------------------------------------------------------------
    # 动作切换
    # ------------------------------------------------------------------

    def _switch_action(self, action_name: str) -> None:
        """通过右键菜单切换动作。"""
        self._animator.play(action_name)
        self._reset_idle_timer()

    # ------------------------------------------------------------------
    # 空闲状态机
    # ------------------------------------------------------------------

    def _reset_idle_timer(self) -> None:
        """重置空闲计时。"""
        self._last_activity_time = time.monotonic()

    def _check_idle(self) -> None:
        """定时检查：长时间无操作则切入待机小憩。

        同时检测鼠标靠近（可选注视行为）。
        """
        if self._animator.get_current_action() == "wave":
            # 挥手是一次性动画，不打断
            return

        now = time.monotonic()
        elapsed = (now - self._last_activity_time) * 1000  # ms

        if elapsed > self._idle_timeout:
            self._animator.play("sleepy")
        else:
            # 空闲状态下随机切换空闲动作
            current = self._animator.get_current_action()
            if current in ("sleepy", "wave"):
                return
            # 每 tick 可能切换（概率 ~1/6 ≈ 每 12 秒切换一次）
            import random as rnd

            if rnd.random() < 0.16:
                self._animator.play(self._animator.get_idle_action())

        # 鼠标靠近检测（简单注视方向——此处为占位，可通过旋转等扩展）
        # 当前仅作为预留接口
        self._check_mouse_proximity()

    def _check_mouse_proximity(self) -> None:
        """检测鼠标是否在宠物附近（预留注视行为）。"""
        cursor_pos = QCursor.pos()
        pet_center = self.mapToGlobal(self.rect().center())
        dx = cursor_pos.x() - pet_center.x()
        dy = cursor_pos.y() - pet_center.y()
        distance = (dx * dx + dy * dy) ** 0.5
        _ = distance  # 目前留空；未来可在此切换"注视"方向

    # ------------------------------------------------------------------
    # 关于 & 退出
    # ------------------------------------------------------------------

    def _show_about(self) -> None:
        """显示关于对话框。"""
        QMessageBox.about(
            self,
            "关于 庄方宜 Q版桌面宠物",
            "庄方宜（出自《明日方舟：终末地》· 麒麟 / 天师）\n\n"
            "角色设计：墨绿色传统服饰 · 黑色长发 · 麒麟角\n"
            "功能：悬浮置顶 · 动画播放 · 鼠标交互 · 语音气泡\n\n"
            "「护生安民，职责所在」",
        )

    def _exit_app(self) -> None:
        """完全退出程序。"""
        from PyQt5.QtWidgets import QApplication

        QApplication.quit()
