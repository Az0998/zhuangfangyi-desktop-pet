"""剪贴板监听与历史（借鉴市面桌宠：历史记录 / 搜索 / 一键粘回 / 关键词反应）。"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QApplication


@dataclass
class ClipboardItem:
    text: str
    kind: str  # text | url | code | path
    ts: float = field(default_factory=time.time)
    preview: str = ""

    def __post_init__(self) -> None:
        if not self.preview:
            one = " ".join(self.text.split())
            self.preview = one[:80] + ("…" if len(one) > 80 else "")


def classify_text(text: str) -> str:
    t = text.strip()
    if re.match(r"^https?://", t, re.I):
        return "url"
    if Path(t).exists() or re.match(r"^[A-Za-z]:\\", t) or t.startswith("/"):
        return "path"
    if any(k in t for k in ("def ", "class ", "import ", "{", "=>", "function ", "console.")):
        return "code"
    return "text"


class ClipboardService(QObject):
    """轮询系统剪贴板，维护历史并发出变化信号。"""

    changed = pyqtSignal(object)  # ClipboardItem

    def __init__(
        self,
        history_path: Path,
        max_items: int = 40,
        poll_ms: int = 700,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._path = history_path
        self._max = max_items
        self._last = ""
        self._items: list[ClipboardItem] = []
        self._enabled = True
        self._load()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(poll_ms)

    @property
    def items(self) -> list[ClipboardItem]:
        return list(self._items)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            for row in raw[-self._max :]:
                self._items.append(
                    ClipboardItem(
                        text=row.get("text", ""),
                        kind=row.get("kind", "text"),
                        ts=float(row.get("ts", time.time())),
                        preview=row.get("preview", ""),
                    )
                )
            if self._items:
                self._last = self._items[-1].text
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            self._items = []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(i) for i in self._items[-self._max :]]
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _poll(self) -> None:
        if not self._enabled:
            return
        app = QApplication.instance() or QGuiApplication.instance()
        if app is None:
            return
        cb = QGuiApplication.clipboard()
        if cb is None:
            return
        text = cb.text() or ""
        if not text.strip() or text == self._last:
            return
        self._last = text
        item = ClipboardItem(text=text, kind=classify_text(text))
        self._items.append(item)
        self._items = self._items[-self._max :]
        self._save()
        self.changed.emit(item)

    def restore(self, text: str) -> None:
        cb = QGuiApplication.clipboard()
        if cb is not None:
            self._last = text
            cb.setText(text)

    def clear(self) -> None:
        self._items.clear()
        self._save()

    def search(self, query: str) -> list[ClipboardItem]:
        q = query.strip().lower()
        if not q:
            return self.items
        return [i for i in self._items if q in i.text.lower() or q in i.kind]


def reaction_for_item(
    item: ClipboardItem,
    reactions: dict[str, list[str]],
    fallback: Callable[[], str] | None = None,
) -> str:
    import random

    pool = reactions.get(item.kind) or reactions.get("text") or []
    if pool:
        return random.choice(pool)
    if fallback:
        return fallback()
    return "嗯……你复制了什么？"
