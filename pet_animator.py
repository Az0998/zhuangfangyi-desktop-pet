"""
pet_animator.py — 动画控制模块。

通过定时器逐帧播放序列帧，使用信号通知更新。
"""

from __future__ import annotations

import random
from pathlib import Path

from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap


class PetAnimator(QObject):
    """动画控制器。加载序列帧图片，通过定时器逐帧切换并发出 frame_changed 信号。"""

    frame_changed = pyqtSignal(QPixmap)

    def __init__(self, assets_dir: Path, config: dict, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._assets_dir = Path(assets_dir)
        self._actions_config: dict = config["animation"]["actions"]
        self._frame_interval: int = config["animation"]["frame_interval_ms"]
        self._idle_actions: list[str] = config["animation"]["idle_actions"]

        self._frames: dict[str, list[QPixmap]] = {}
        self._current_action: str = ""
        self._current_frame_index: int = 0
        self._playing: bool = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)

        self._load_all_frames()

    # ------------------------------------------------------------------
    # 图片加载
    # ------------------------------------------------------------------

    def _load_all_frames(self) -> None:
        """遍历配置中的每个动作，从 assets 子目录加载 PNG 序列帧。"""
        for action_name, info in self._actions_config.items():
            dir_name: str = info["dir"]
            action_dir = self._assets_dir / dir_name
            frames: list[QPixmap] = []

            if action_dir.is_dir():
                # 按文件名自然排序（frame_01, frame_02, …）
                for fpath in sorted(action_dir.iterdir()):
                    if fpath.suffix.lower() == ".png":
                        pix = QPixmap(str(fpath))
                        if not pix.isNull():
                            frames.append(pix)

            if not frames:
                # 兜底：创建一张空白占位图避免空转
                fallback = QPixmap(120, 160)
                fallback.fill(Qt.GlobalColor.transparent)  # type: ignore[attr-defined]
                frames.append(fallback)

            self._frames[action_name] = frames

    # ------------------------------------------------------------------
    # 公开控制接口
    # ------------------------------------------------------------------

    def play(self, action_name: str) -> None:
        """播放指定动作的动画序列。

        Args:
            action_name: 动作名称（需在 config.json actions 中定义）。
        """
        if action_name not in self._frames:
            return

        self._timer.stop()
        self._current_action = action_name
        self._current_frame_index = 0
        self._playing = True

        # 发射第一帧
        self.frame_changed.emit(self._frames[action_name][0])
        self._timer.start(self._frame_interval)

    def stop(self) -> None:
        """停止所有动画，停留在当前帧。"""
        self._timer.stop()
        self._playing = False

    def pause(self) -> None:
        """暂停动画（定时器停，帧不变）。"""
        self._timer.stop()

    def resume(self) -> None:
        """继续播放被暂停的动画。"""
        if self._playing and self._current_action:
            self._timer.start(self._frame_interval)

    def get_current_action(self) -> str:
        """返回当前播放的动作名称。"""
        return self._current_action

    def get_idle_action(self) -> str:
        """从空闲动作列表中随机选取一个。"""
        return random.choice(self._idle_actions)

    # ------------------------------------------------------------------
    # 内部定时器回调
    # ------------------------------------------------------------------

    def _next_frame(self) -> None:
        """定时器回调：切到下一帧并发射信号。"""
        if not self._current_action:
            return

        frames = self._frames.get(self._current_action)
        if not frames:
            return

        frame_count = len(frames)
        self._current_frame_index = (self._current_frame_index + 1) % frame_count
        self.frame_changed.emit(frames[self._current_frame_index])
