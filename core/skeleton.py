"""简易 2D 骨骼系统：父子关节 + 局部旋转，QPainter 渲染部件。"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter, QPixmap, QTransform


@dataclass
class Bone:
    name: str
    parent: str | None
    length: float
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0  # degrees, local
    z: int = 0
    part: str | None = None
    pivot_x: float = 0.0
    pivot_y: float = 0.0
    children: list[str] = field(default_factory=list)


@dataclass
class Pose:
    """一组骨骼局部旋转/偏移覆盖。"""

    rotations: dict[str, float] = field(default_factory=dict)
    offsets: dict[str, tuple[float, float]] = field(default_factory=dict)

    def blend(self, other: "Pose", t: float) -> "Pose":
        t = max(0.0, min(1.0, t))
        keys = set(self.rotations) | set(other.rotations)
        rotations = {}
        for k in keys:
            a = self.rotations.get(k, 0.0)
            b = other.rotations.get(k, 0.0)
            # shortest-angle lerp
            diff = (b - a + 180) % 360 - 180
            rotations[k] = a + diff * t
        off_keys = set(self.offsets) | set(other.offsets)
        offsets = {}
        for k in off_keys:
            ax, ay = self.offsets.get(k, (0.0, 0.0))
            bx, by = other.offsets.get(k, (0.0, 0.0))
            offsets[k] = (ax + (bx - ax) * t, ay + (by - ay) * t)
        return Pose(rotations=rotations, offsets=offsets)


class Skeleton:
    """骨骼层级与部件贴图。"""

    def __init__(self, definition: dict[str, Any], parts: dict[str, QPixmap] | None = None) -> None:
        self.width = int(definition.get("width", 180))
        self.height = int(definition.get("height", 240))
        self.origin = definition.get("origin", {"x": self.width / 2, "y": self.height * 0.72})
        self.bones: dict[str, Bone] = {}
        self.base_rotations: dict[str, float] = {}
        self._base_xy: dict[str, tuple[float, float]] = {}
        self.parts: dict[str, QPixmap] = parts or {}
        self._build(definition.get("bones", []))

    def _build(self, bone_defs: list[dict[str, Any]]) -> None:
        for b in bone_defs:
            bone = Bone(
                name=b["name"],
                parent=b.get("parent"),
                length=float(b.get("length", 20)),
                x=float(b.get("x", 0)),
                y=float(b.get("y", 0)),
                rotation=float(b.get("rotation", 0)),
                z=int(b.get("z", 0)),
                part=b.get("part"),
                pivot_x=float(b.get("pivot_x", 0)),
                pivot_y=float(b.get("pivot_y", 0)),
            )
            self.bones[bone.name] = bone
            self.base_rotations[bone.name] = bone.rotation
            self._base_xy[bone.name] = (bone.x, bone.y)
        for bone in self.bones.values():
            if bone.parent and bone.parent in self.bones:
                self.bones[bone.parent].children.append(bone.name)

    def set_parts(self, parts: dict[str, QPixmap]) -> None:
        self.parts = parts

    def apply_pose(self, pose: Pose) -> None:
        for name, bone in self.bones.items():
            bone.rotation = self.base_rotations.get(name, 0.0) + pose.rotations.get(name, 0.0)
            ox, oy = pose.offsets.get(name, (0.0, 0.0))
            bx, by = self._base_xy.get(name, (bone.x, bone.y))
            bone.x = bx + ox
            bone.y = by + oy

    def world_transform(self, name: str) -> QTransform:
        """累积父链得到世界变换（原点在画布 origin）。"""
        chain: list[Bone] = []
        cur: str | None = name
        while cur:
            bone = self.bones[cur]
            chain.append(bone)
            cur = bone.parent
        chain.reverse()

        t = QTransform()
        t.translate(self.origin["x"], self.origin["y"])
        for bone in chain:
            t.translate(bone.x, bone.y)
            t.rotate(bone.rotation)
        return t

    def render(self, look_dx: float = 0.0, look_dy: float = 0.0, blush: float = 0.0) -> QPixmap:
        """渲染当前姿势到透明画布。look_* 影响头/眼微移。"""
        canvas = QPixmap(self.width, self.height)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        ordered = sorted(self.bones.values(), key=lambda b: b.z)
        for bone in ordered:
            if not bone.part or bone.part not in self.parts:
                continue
            pix = self.parts[bone.part]
            if pix.isNull():
                continue

            transform = self.world_transform(bone.name)
            # 注视：头与身体微移
            if bone.name in ("head", "face", "eyes", "ear_l", "ear_r", "hood", "body"):
                transform.translate(look_dx * (5.0 if bone.name == "body" else 4.0), look_dy * 3.0)
            if bone.name == "eyes":
                transform.translate(look_dx * 2.5, look_dy * 2.0)

            painter.save()
            painter.setTransform(transform, combine=False)
            painter.drawPixmap(
                QPointF(-bone.pivot_x, -bone.pivot_y),
                pix,
            )
            painter.restore()

        # 害羞红晕叠加在脸上
        if blush > 0.05 and "blush" in self.parts:
            painter.save()
            bone_name = "body" if "body" in self.bones else ("face" if "face" in self.bones else "head")
            transform = self.world_transform(bone_name)
            painter.setTransform(transform, combine=False)
            painter.setOpacity(min(1.0, blush))
            blush_pix = self.parts["blush"]
            # 大致贴在头脸位置
            bh = self.bones.get(bone_name)
            px = (bh.pivot_x if bh else blush_pix.width() / 2) - blush_pix.width() / 2
            py = -((bh.pivot_y if bh else 80) * 0.55)
            painter.drawPixmap(QPointF(px, py), blush_pix)
            painter.setOpacity(1.0)
            painter.restore()

        painter.end()
        return canvas

    def clone_definition(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "origin": copy.deepcopy(self.origin),
            "bones": [
                {
                    "name": b.name,
                    "parent": b.parent,
                    "length": b.length,
                    "x": self._base_xy.get(b.name, (b.x, b.y))[0],
                    "y": self._base_xy.get(b.name, (b.x, b.y))[1],
                    "rotation": self.base_rotations.get(b.name, 0.0),
                    "z": b.z,
                    "part": b.part,
                    "pivot_x": b.pivot_x,
                    "pivot_y": b.pivot_y,
                }
                for b in self.bones.values()
            ],
        }
