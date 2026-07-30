"""宠物主窗口：骨骼互动、画风切换、剪贴板、日程、AI 对话。"""

from __future__ import annotations

import random
import time
from pathlib import Path

from PyQt5.QtCore import QPoint, QThread, Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCursor, QMouseEvent, QPixmap
from PyQt5.QtWidgets import QLabel, QMenu, QMessageBox, QVBoxLayout, QWidget

from core.ai_client import AIClient
from core.character import CharacterPack, list_characters, load_character
from core.clipboard_service import ClipboardItem, ClipboardService, reaction_for_item
from core.schedule_service import HealthConfig, ScheduleService
from core.skeletal_animator import SkeletalAnimator
from ui.bubble import BubbleWidget
from ui.chat_panel import ChatPanel
from ui.clipboard_panel import ClipboardPanel
from ui.schedule_panel import SchedulePanel


class _ChatWorker(QThread):
    finished_ok = pyqtSignal(str)
    finished_err = pyqtSignal(str)

    def __init__(self, client: AIClient, text: str, fallbacks: list[str], parent=None) -> None:
        super().__init__(parent)
        self._client = client
        self._text = text
        self._fallbacks = fallbacks

    def run(self) -> None:
        try:
            if self._client.configured:
                reply = self._client.chat(self._text)
            else:
                reply = self._client.offline_reply(self._text, self._fallbacks)
            self.finished_ok.emit(reply)
        except Exception as e:  # noqa: BLE001
            try:
                reply = self._client.offline_reply(self._text, self._fallbacks)
                self.finished_ok.emit(f"{reply}\n（离线兜底：{e}）")
            except Exception:
                self.finished_err.emit(str(e))


class PetWindow(QWidget):
    character_changed = pyqtSignal(str)

    def __init__(
        self,
        animator: SkeletalAnimator,
        character: CharacterPack,
        config: dict,
        base_dir: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._animator = animator
        self._character = character
        self._config = config
        self._base_dir = base_dir
        self._data_dir = base_dir / "data"
        self._data_dir.mkdir(exist_ok=True)

        self._ai = AIClient.from_config(config.get("ai", {}), character.system_prompt)
        self._idle_timeout = int(config.get("animation", {}).get("idle_timeout_ms", 45000))
        self._mouse_proximity = int(config.get("mouse_proximity_px", 140))
        self._bubble_ms = int(config.get("bubble", {}).get("display_ms", 3400))
        self._walk_enabled = bool(config.get("behavior", {}).get("auto_walk", True))
        self._clipboard_react = bool(config.get("clipboard", {}).get("react", True))

        cb_cfg = config.get("clipboard", {})
        self._clipboard = ClipboardService(
            self._data_dir / "clipboard_history.json",
            max_items=int(cb_cfg.get("max_items", 40)),
            poll_ms=int(cb_cfg.get("poll_ms", 700)),
            parent=self,
        )
        self._clipboard.changed.connect(self._on_clipboard)

        hcfg = config.get("health", {})
        self._schedule = ScheduleService(
            self._data_dir / "schedule.json",
            HealthConfig(
                water_min=int(hcfg.get("water_min", 45)),
                eye_min=int(hcfg.get("eye_min", 30)),
                rest_min=int(hcfg.get("rest_min", 60)),
                enabled=bool(hcfg.get("enabled", True)),
            ),
            parent=self,
        )
        self._schedule.reminder.connect(self._on_reminder)

        self._drag_offset = QPoint()
        self._dragging = False
        self._last_activity = time.monotonic()
        self._current_bubble: BubbleWidget | None = None
        self._chat_panel: ChatPanel | None = None
        self._clip_panel: ClipboardPanel | None = None
        self._sched_panel: SchedulePanel | None = None
        self._chat_worker: _ChatWorker | None = None
        self._walk_dir = 1
        self._click_count = 0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self._image_label = QLabel(self)
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._image_label)

        win = config.get("window", {})
        self.move(win.get("default_x", 420), win.get("default_y", 360))

        self._animator.frame_changed.connect(self._on_frame_changed)
        self._animator.action_finished.connect(self._on_action_finished)
        self._animator.play_chain("greet_flow")

        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._on_behavior_tick)
        self._idle_timer.start(500)

        self._look_timer = QTimer(self)
        self._look_timer.timeout.connect(self._update_look)
        self._look_timer.start(50)

        if self._walk_enabled:
            self._walk_timer = QTimer(self)
            self._walk_timer.timeout.connect(self._auto_walk_step)
            self._walk_timer.start(40)

        QTimer.singleShot(500, self._greet)

    # ------------------------------------------------------------------
    def set_character(self, character: CharacterPack) -> None:
        self._character = character
        self._ai.set_system_prompt(character.system_prompt)
        self._ai.clear_history()
        self._animator.reload_character(character)
        if self._chat_panel is not None:
            self._chat_panel.set_character(
                character.name, character.colors.get("primary", "#C23B3B")
            )
        self.character_changed.emit(character.id)
        self._show_bubble(random.choice(character.greetings or character.bubble_lines))

    def set_art_style(self, style: str) -> None:
        pack = self._character.with_art_style(style)
        self.set_character(pack)
        self._show_bubble(
            "像素风，清晰！……才不是说我喜欢复古。"
            if style == "pixel"
            else "动漫风……这样看耳朵更清楚了啦。"
        )

    # ------------------------------------------------------------------
    @pyqtSlot(QPixmap)
    def _on_frame_changed(self, pixmap: QPixmap) -> None:
        self._image_label.setPixmap(pixmap)
        self._image_label.resize(pixmap.size())
        self.resize(pixmap.size())

    @pyqtSlot(str)
    def _on_action_finished(self, _action: str) -> None:
        # 动作链由 animator 内部队列接管；此处不强制打断
        return

    # ------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            self._dragging = False
            self._bump_activity()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPos() - self._drag_offset)
            self._dragging = True
            self._bump_activity()
            if self._animator.get_current_action() != "walk":
                self._animator.play("walk")
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._dragging:
                self._on_click()
            else:
                self._animator.play("idle")
            self._dragging = False
            self._bump_activity()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_chat()
            self._bump_activity()
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event) -> None:
        accent = self._character.colors.get("primary", "#C23B3B")
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #fff8f5; border: 1px solid #e0b8b0; border-radius: 6px; }"
            "QMenu::item { padding: 7px 22px; }"
            f"QMenu::item:selected {{ background: {accent}; color: white; }}"
        )

        menu.addAction("和她聊天…").triggered.connect(self.open_chat)
        menu.addAction("剪贴板历史…").triggered.connect(self.open_clipboard)
        menu.addAction("日程 / 健康提醒…").triggered.connect(self.open_schedule)

        style_menu = menu.addMenu("画风")
        for style in self._character.variants:
            label = {"anime": "动漫版", "pixel": "像素版"}.get(style, style)
            if style == self._character.art_style:
                label = f"✓ {label}"
            style_menu.addAction(label).triggered.connect(
                lambda checked=False, s=style: self.set_art_style(s)
            )

        act_menu = menu.addMenu("切换动作")
        for name in self._animator.list_actions():
            act_menu.addAction(name).triggered.connect(
                lambda checked=False, n=name: self._switch_action(n)
            )
        chain_menu = menu.addMenu("动作链")
        for cname in self._character.animations.get("chains", {}):
            chain_menu.addAction(cname).triggered.connect(
                lambda checked=False, n=cname: self._animator.play_chain(n)
            )

        char_menu = menu.addMenu("更换角色")
        for info in list_characters(self._base_dir):
            label = info["name"]
            if info["id"] == self._character.id:
                label = f"✓ {label}"
            char_menu.addAction(label).triggered.connect(
                lambda checked=False, cid=info["id"]: self._switch_character(cid)
            )

        menu.addSeparator()
        menu.addAction("关于").triggered.connect(self._show_about)
        menu.addAction("退出").triggered.connect(self._exit_app)
        menu.exec_(event.globalPos())
        self._bump_activity()

    # ------------------------------------------------------------------
    def _on_click(self) -> None:
        self._click_count += 1
        lines = self._character.bubble_lines
        text = random.choice(lines) if lines else "……"
        if self._click_count % 7 == 0:
            self._animator.play_chain("praise_flow")
            self._animator.pulse_blush(1.0)
            text = random.choice(self._character.moe_hooks.get("praise", lines))
        elif self._click_count % 5 == 0:
            self._animator.play_once("jump")
            text = random.choice(self._character.moe_hooks.get("hero", lines))
        elif self._click_count % 3 == 0:
            self._animator.play_chain("greet_flow")
            self._animator.pulse_blush(0.45)
        else:
            self._animator.play_once("wave")
        self._show_bubble(text)

    def _show_bubble(self, text: str) -> None:
        if self._current_bubble is not None:
            self._current_bubble.close()
        accent = self._character.colors.get("primary", "#C23B3B")
        bubble = BubbleWidget(text, self._bubble_ms, accent, self)
        bubble.position_above(self)
        bubble.show()
        self._current_bubble = bubble

    def _greet(self) -> None:
        greetings = self._character.greetings or self._character.bubble_lines
        if greetings:
            self._show_bubble(random.choice(greetings))

    def _switch_action(self, name: str) -> None:
        anim = self._character.animations.get("animations", {}).get(name, {})
        if anim.get("loop", True):
            self._animator.play(name)
        else:
            self._animator.play_once(name)
        self._bump_activity()

    def _switch_character(self, character_id: str) -> None:
        if character_id == self._character.id:
            return
        try:
            style = self._config.get("art_style") or self._character.art_style
            pack = load_character(character_id, self._base_dir, art_style=style)
        except FileNotFoundError as e:
            QMessageBox.warning(self, "更换角色失败", str(e))
            return
        self.set_character(pack)

    # ------------------------------------------------------------------
    def open_chat(self) -> None:
        if self._chat_panel is None:
            accent = self._character.colors.get("primary", "#C23B3B")
            self._chat_panel = ChatPanel(self._character.name, accent)
            self._chat_panel.message_submitted.connect(self._on_chat_submit)
            self._chat_panel.closed.connect(lambda: setattr(self, "_chat_panel", None))
        self._chat_panel.move(self.mapToGlobal(QPoint(self.width() + 8, 0)))
        self._chat_panel.show()
        self._chat_panel.raise_()
        self._animator.play_once("curious")
        self._bump_activity()

    def open_clipboard(self) -> None:
        if self._clip_panel is None:
            accent = self._character.colors.get("primary", "#C23B3B")
            self._clip_panel = ClipboardPanel(self._clipboard, accent)
            self._clip_panel.restore_requested.connect(
                lambda _t: self._show_bubble("粘回去了。谢我就行……哼。")
            )
            self._clip_panel.closed.connect(lambda: setattr(self, "_clip_panel", None))
        self._clip_panel.refresh()
        self._clip_panel.move(self.mapToGlobal(QPoint(self.width() + 8, 0)))
        self._clip_panel.show()
        self._clip_panel.raise_()
        self._animator.play_chain("copy_react")
        self._bump_activity()

    def open_schedule(self) -> None:
        if self._sched_panel is None:
            accent = self._character.colors.get("primary", "#C23B3B")
            self._sched_panel = SchedulePanel(self._schedule, accent)
            self._sched_panel.closed.connect(lambda: setattr(self, "_sched_panel", None))
        self._sched_panel.refresh()
        self._sched_panel.move(self.mapToGlobal(QPoint(self.width() + 8, 40)))
        self._sched_panel.show()
        self._sched_panel.raise_()
        self._animator.play_once("think")
        self._bump_activity()

    def _on_chat_submit(self, text: str) -> None:
        if self._chat_panel is None:
            return
        self._chat_panel.append_user(text)
        self._chat_panel.set_busy(True)
        self._animator.play_once("curious")
        self._bump_activity()
        low = text.lower()
        if any(k in low for k in ("可爱", "漂亮", "喜欢", "萌", "耳朵", "尾巴")):
            self._animator.play_chain("praise_flow")
            self._animator.pulse_blush(0.95)
        worker = _ChatWorker(self._ai, text, self._character.bubble_lines, self)
        worker.finished_ok.connect(self._on_chat_ok)
        worker.finished_err.connect(self._on_chat_err)
        self._chat_worker = worker
        worker.start()

    @pyqtSlot(str)
    def _on_chat_ok(self, reply: str) -> None:
        if self._chat_panel is not None:
            self._chat_panel.append_pet(self._character.name, reply)
            self._chat_panel.set_busy(False)
        self._show_bubble(reply.split("\n")[0][:60])
        if any(k in reply for k in ("脸", "羞", "才不", "耳朵", "尾巴")):
            self._animator.play_once("shy")
            self._animator.pulse_blush(0.8)
        else:
            self._animator.play_once("happy")

    @pyqtSlot(str)
    def _on_chat_err(self, err: str) -> None:
        if self._chat_panel is not None:
            self._chat_panel.append_pet(self._character.name, f"……通讯中断了。({err})")
            self._chat_panel.set_busy(False)

    @pyqtSlot(object)
    def _on_clipboard(self, item: ClipboardItem) -> None:
        if not self._clipboard_react:
            return
        if self._clip_panel is not None:
            self._clip_panel.refresh()
        text = reaction_for_item(item, self._character.clipboard_reactions)
        self._animator.play_chain("copy_react")
        self._show_bubble(text)
        self._bump_activity()

    @pyqtSlot(str, str)
    def _on_reminder(self, kind: str, message: str) -> None:
        lines = self._character.schedule_lines.get(kind) or []
        text = random.choice(lines) if lines and random.random() < 0.5 else message
        self._animator.play_sequence(["alert", "think"])
        self._show_bubble(text)
        self._bump_activity()

    # ------------------------------------------------------------------
    def _bump_activity(self) -> None:
        self._last_activity = time.monotonic()

    def _on_behavior_tick(self) -> None:
        action = self._animator.get_current_action()
        busy = {"wave", "happy", "shy", "jump", "stretch", "blink", "alert"}
        if action in busy or self._dragging:
            return
        elapsed = (time.monotonic() - self._last_activity) * 1000
        if elapsed > self._idle_timeout:
            if action != "sleepy":
                self._animator.play("sleepy")
            return
        if action == "sleepy":
            self._animator.play_chain("wake_up")
        elif random.random() < 0.06:
            self._animator.play(self._animator.get_idle_action())

    def _update_look(self) -> None:
        cursor = QCursor.pos()
        center = self.mapToGlobal(self.rect().center())
        dx = cursor.x() - center.x()
        dy = cursor.y() - center.y()
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < self._mouse_proximity * 3:
            self._animator.set_look(dx / 180.0, dy / 180.0)
        else:
            self._animator.set_look(0.0, 0.0)

    def _auto_walk_step(self) -> None:
        if self._dragging or self._animator.get_current_action() != "walk":
            return
        screen = self.screen().availableGeometry() if self.screen() else None
        if screen is None:
            return
        x = self.x() + self._walk_dir * 2
        if x < screen.left() + 10:
            self._walk_dir = 1
            x = screen.left() + 10
        elif x > screen.right() - self.width() - 10:
            self._walk_dir = -1
            x = screen.right() - self.width() - 10
        self.move(x, self.y())

    def _show_about(self) -> None:
        c = self._character
        QMessageBox.about(
            self,
            f"关于 {c.name}",
            f"{c.name}（{c.title}）\n画风：{c.art_style}\n\n{c.about}\n\n"
            "操作：\n"
            "· 单击互动 / 拖拽带走 / 双击聊天\n"
            "· 右键：画风、剪贴板、日程、动作链\n"
            "· 复制文本时她会接话并记入历史\n\n"
            "「才不是因为想陪你才留下来的。」",
        )

    def _exit_app(self) -> None:
        from PyQt5.QtWidgets import QApplication

        QApplication.quit()
