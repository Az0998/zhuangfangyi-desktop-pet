"""骨骼关键帧动画播放器。"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap

from .character import CharacterPack
from .skeleton import Pose, Skeleton


def _ease(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


class SkeletalAnimator(QObject):
    """根据 animations.json 插值骨骼姿势并输出帧。"""

    frame_changed = pyqtSignal(QPixmap)
    action_finished = pyqtSignal(str)

    def __init__(
        self,
        character: CharacterPack,
        parent: QObject | None = None,
        tick_ms: int = 33,
    ) -> None:
        super().__init__(parent)
        self._character = character
        self._tick_ms = tick_ms
        self._parts = self._load_parts(character)
        self._skeleton = Skeleton(character.skeleton, self._parts)
        self._animations: dict[str, Any] = character.animations.get("animations", {})
        self._idle_actions: list[str] = character.animations.get(
            "idle_actions", ["idle", "curious", "happy"]
        )
        self._chains: dict[str, list[str]] = character.animations.get("chains", {})

        self._current_action = "idle"
        self._elapsed = 0.0
        self._loop = True
        self._playing = False
        self._look_dx = 0.0
        self._look_dy = 0.0
        self._blush = 0.0
        self._target_blush = 0.0
        self._one_shot_return = "idle"
        self._queue: list[str] = []
        self._blink_cd = 2.5

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

    # ------------------------------------------------------------------
    @staticmethod
    def _load_parts(character: CharacterPack) -> dict[str, QPixmap]:
        parts: dict[str, QPixmap] = {}
        parts_dir = character.parts_dir
        if not parts_dir.is_dir():
            return parts
        for path in parts_dir.glob("*.png"):
            pix = QPixmap(str(path))
            if not pix.isNull():
                parts[path.stem] = pix
        return parts

    def reload_character(self, character: CharacterPack) -> None:
        self._character = character
        self._parts = self._load_parts(character)
        self._skeleton = Skeleton(character.skeleton, self._parts)
        self._animations = character.animations.get("animations", {})
        self._idle_actions = character.animations.get(
            "idle_actions", ["idle", "curious", "happy"]
        )
        self._chains = character.animations.get("chains", {})
        self._queue.clear()
        self.play("idle")

    @property
    def skeleton(self) -> Skeleton:
        return self._skeleton

    def list_actions(self) -> list[str]:
        return list(self._animations.keys())

    def play(self, action_name: str, loop: bool | None = None) -> None:
        if action_name not in self._animations:
            action_name = "idle" if "idle" in self._animations else next(iter(self._animations), "")
            if not action_name:
                return
        anim = self._animations[action_name]
        self._current_action = action_name
        self._elapsed = 0.0
        self._loop = anim.get("loop", True) if loop is None else loop
        self._playing = True
        if not self._timer.isActive():
            self._timer.start(self._tick_ms)
        self._emit_frame()

    def play_once(self, action_name: str, return_to: str = "idle") -> None:
        self._queue.clear()
        self._one_shot_return = return_to
        self.play(action_name, loop=False)

    def play_chain(self, chain_name: str, return_to: str = "idle") -> None:
        """播放命名动作链，例如 greet_flow = [wave, happy]。"""
        steps = list(self._chains.get(chain_name, []))
        if not steps:
            self.play_once(chain_name if chain_name in self._animations else "wave", return_to)
            return
        self._one_shot_return = return_to
        first, *rest = steps
        self._queue = rest
        self.play(first, loop=False)

    def play_sequence(self, actions: list[str], return_to: str = "idle") -> None:
        if not actions:
            return
        self._one_shot_return = return_to
        first, *rest = actions
        self._queue = rest
        self.play(first, loop=False)

    def stop(self) -> None:
        self._timer.stop()
        self._playing = False

    def get_current_action(self) -> str:
        return self._current_action

    def get_idle_action(self) -> str:
        return random.choice(self._idle_actions)

    def set_look(self, dx: float, dy: float) -> None:
        self._look_dx = max(-1.0, min(1.0, dx))
        self._look_dy = max(-1.0, min(1.0, dy))

    def set_blush(self, amount: float) -> None:
        self._target_blush = max(0.0, min(1.0, amount))

    def pulse_blush(self, amount: float = 0.85) -> None:
        self._target_blush = max(self._target_blush, amount)

    # ------------------------------------------------------------------
    def _pose_at(self, action: str, t_sec: float) -> Pose:
        anim = self._animations[action]
        duration = float(anim.get("duration", 1.0))
        keyframes: list[dict[str, Any]] = anim.get("keyframes", [])
        if not keyframes:
            return Pose()
        if duration <= 0:
            return self._kf_to_pose(keyframes[0])

        local_t = t_sec % duration if self._loop else min(t_sec, duration)
        # keyframe times are 0..1
        norm = local_t / duration
        if norm <= keyframes[0].get("t", 0.0):
            return self._kf_to_pose(keyframes[0])
        if norm >= keyframes[-1].get("t", 1.0):
            return self._kf_to_pose(keyframes[-1])

        for i in range(len(keyframes) - 1):
            a, b = keyframes[i], keyframes[i + 1]
            ta, tb = float(a.get("t", 0)), float(b.get("t", 1))
            if ta <= norm <= tb:
                u = 0.0 if tb == ta else (norm - ta) / (tb - ta)
                return self._kf_to_pose(a).blend(self._kf_to_pose(b), _ease(u))
        return self._kf_to_pose(keyframes[-1])

    @staticmethod
    def _kf_to_pose(kf: dict[str, Any]) -> Pose:
        rotations = {k: float(v) for k, v in kf.get("rotations", {}).items()}
        offsets = {
            k: (float(v[0]), float(v[1])) for k, v in kf.get("offsets", {}).items()
        }
        return Pose(rotations=rotations, offsets=offsets)

    def _on_tick(self) -> None:
        if not self._playing:
            return
        dt = self._tick_ms / 1000.0
        self._elapsed += dt

        # blush decay / approach
        if self._blush < self._target_blush:
            self._blush = min(self._target_blush, self._blush + dt * 2.5)
        else:
            self._target_blush = max(0.0, self._target_blush - dt * 0.35)
            self._blush = max(self._target_blush, self._blush - dt * 0.5)

        anim = self._animations.get(self._current_action, {})
        duration = float(anim.get("duration", 1.0))
        if (not self._loop) and self._elapsed >= duration:
            finished = self._current_action
            self.action_finished.emit(finished)
            if self._queue:
                nxt = self._queue.pop(0)
                self.play(nxt, loop=False)
            else:
                self.play(self._one_shot_return)
            return

        # 待机时偶发眨眼
        if self._current_action == "idle" and "blink" in self._animations:
            self._blink_cd -= dt
            if self._blink_cd <= 0:
                self._blink_cd = random.uniform(2.8, 5.5)
                self.play_once("blink", return_to="idle")
                return

        self._emit_frame()

    def _emit_frame(self) -> None:
        pose = self._pose_at(self._current_action, self._elapsed)
        # 英雄全身图模式：把各关节动作烘焙到可见的 body 上
        has_body = "body" in self._parts and not self._parts["body"].isNull()
        breath = math.sin(self._elapsed * 2.4) * (3.0 if has_body else 1.2)
        sway = math.sin(self._elapsed * 1.7) * (1.5 if has_body else 0.0)

        if has_body:
            tx, ty = pose.offsets.get("torso", (0.0, 0.0))
            bx, by = pose.offsets.get("body", (0.0, 0.0))
            hx, hy = pose.offsets.get("head", (0.0, 0.0))
            # 走路左右晃、跳跃上下明显
            leg = pose.rotations.get("leg_l", 0.0) - pose.rotations.get("leg_r", 0.0)
            arm = pose.rotations.get("arm_r", 0.0)
            head_r = pose.rotations.get("head", 0.0)
            tail_r = pose.rotations.get("tail", 0.0)
            body_r = pose.rotations.get("body", 0.0)
            pose.offsets["body"] = (
                bx + tx + hx + sway + leg * 0.08,
                by + ty + hy * 0.5 + breath,
            )
            pose.rotations["body"] = (
                body_r
                + head_r * 0.45
                + arm * 0.04
                + tail_r * 0.03
                + math.sin(self._elapsed * 3.0) * (2.0 if self._current_action == "walk" else 0.6)
            )
            # 开心/跳跃额外压扁感用更大上下位移已在关键帧里
        else:
            if "torso" in pose.offsets:
                ox, oy = pose.offsets["torso"]
                pose.offsets["torso"] = (ox, oy + breath)
            else:
                pose.offsets["torso"] = (0.0, breath)

        self._skeleton.apply_pose(pose)
        frame = self._skeleton.render(self._look_dx, self._look_dy, self._blush)
        self.frame_changed.emit(frame)
