"""日程与健康提醒（借鉴市面桌宠：喝水/护眼/休息 + 自定义日程）。"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


@dataclass
class ScheduleItem:
    id: str
    title: str
    kind: str  # once | daily | interval
    # once/daily: "HH:MM"；interval: minutes as string e.g. "45"
    when: str
    enabled: bool = True
    message: str = ""
    last_fired: str = ""  # YYYY-MM-DD or ISO for interval


@dataclass
class HealthConfig:
    water_min: int = 45
    eye_min: int = 30
    rest_min: int = 60
    enabled: bool = True


class ScheduleService(QObject):
    reminder = pyqtSignal(str, str)  # kind, message

    def __init__(
        self,
        data_path: Path,
        health: HealthConfig | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._path = data_path
        self.health = health or HealthConfig()
        self.items: list[ScheduleItem] = []
        self._interval_marks: dict[str, float] = {}
        self._health_marks = {
            "water": time.monotonic(),
            "eye": time.monotonic(),
            "rest": time.monotonic(),
        }
        self._load()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(15_000)

    def _load(self) -> None:
        if not self._path.exists():
            self.items = self._default_items()
            self._save()
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            health = raw.get("health", {})
            self.health = HealthConfig(
                water_min=int(health.get("water_min", 45)),
                eye_min=int(health.get("eye_min", 30)),
                rest_min=int(health.get("rest_min", 60)),
                enabled=bool(health.get("enabled", True)),
            )
            self.items = []
            for row in raw.get("items", []):
                self.items.append(
                    ScheduleItem(
                        id=row.get("id") or str(uuid.uuid4()),
                        title=row.get("title", "提醒"),
                        kind=row.get("kind", "daily"),
                        when=row.get("when", "09:00"),
                        enabled=bool(row.get("enabled", True)),
                        message=row.get("message", ""),
                        last_fired=row.get("last_fired", ""),
                    )
                )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            self.items = self._default_items()

    @staticmethod
    def _default_items() -> list[ScheduleItem]:
        return [
            ScheduleItem(
                id=str(uuid.uuid4()),
                title="上午开工",
                kind="daily",
                when="09:30",
                message="该开工了——不是我催你，是日程表催你。",
            ),
            ScheduleItem(
                id=str(uuid.uuid4()),
                title="午饭",
                kind="daily",
                when="12:00",
                message="午饭！狼也要吃饭的，你也是。",
            ),
            ScheduleItem(
                id=str(uuid.uuid4()),
                title="傍晚收工提醒",
                kind="daily",
                when="18:30",
                message="……可以考虑歇一会儿了。别仗着我陪着就熬夜。",
            ),
        ]

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "health": asdict(self.health),
            "items": [asdict(i) for i in self.items],
        }
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_item(self, title: str, kind: str, when: str, message: str = "") -> ScheduleItem:
        item = ScheduleItem(
            id=str(uuid.uuid4()),
            title=title,
            kind=kind,
            when=when,
            message=message or title,
        )
        self.items.append(item)
        self._save()
        return item

    def remove_item(self, item_id: str) -> None:
        self.items = [i for i in self.items if i.id != item_id]
        self._save()

    def toggle_item(self, item_id: str, enabled: bool) -> None:
        for i in self.items:
            if i.id == item_id:
                i.enabled = enabled
                break
        self._save()

    def update_health(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if hasattr(self.health, k):
                setattr(self.health, k, v)
        self._save()

    def _tick(self) -> None:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        hm = now.strftime("%H:%M")

        for item in self.items:
            if not item.enabled:
                continue
            if item.kind in ("once", "daily"):
                if item.when == hm and item.last_fired != today:
                    item.last_fired = today
                    if item.kind == "once":
                        item.enabled = False
                    self._save()
                    msg = item.message or item.title
                    self.reminder.emit(item.kind, msg)
            elif item.kind == "interval":
                try:
                    mins = max(1, int(item.when))
                except ValueError:
                    continue
                last = self._interval_marks.get(item.id, time.monotonic())
                if time.monotonic() - last >= mins * 60:
                    self._interval_marks[item.id] = time.monotonic()
                    self.reminder.emit("interval", item.message or item.title)

        if self.health.enabled:
            mono = time.monotonic()
            checks = [
                ("water", self.health.water_min, "喝口水吧。狼群行军也要补水……你也是。"),
                ("eye", self.health.eye_min, "眼睛歇一下！看远处二十秒——这是巡逻观察训练。"),
                ("rest", self.health.rest_min, "起来活动活动。别窝着，我可看不下去。"),
            ]
            for key, mins, msg in checks:
                if mono - self._health_marks[key] >= mins * 60:
                    self._health_marks[key] = mono
                    self.reminder.emit(key, msg)

    def snooze_health(self, kind: str) -> None:
        if kind in self._health_marks:
            self._health_marks[kind] = time.monotonic()
