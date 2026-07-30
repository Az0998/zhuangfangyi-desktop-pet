"""语音气泡。"""

from __future__ import annotations

from PyQt5.QtCore import QPoint, Qt, QTimer
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class BubbleWidget(QWidget):
    def __init__(
        self,
        text: str,
        display_ms: int = 3200,
        accent: str = "#C23B3B",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._label = QLabel(text, self)
        self._label.setWordWrap(True)
        self._label.setMaximumWidth(260)
        self._label.setStyleSheet(
            f"background-color: rgba(255, 248, 245, 230);"
            f"color: #3a2a2a;"
            f"border: 2px solid {accent};"
            f"border-radius: 12px;"
            f"padding: 10px 14px;"
            f"font-size: 13px;"
            f"font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;"
        )
        self._label.adjustSize()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self.resize(self._label.sizeHint().width() + 8, self._label.sizeHint().height() + 8)

        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self.close)
        self._close_timer.start(display_ms)

    def position_above(self, widget: QWidget, offset_y: int = 8) -> None:
        parent_pos = widget.mapToGlobal(QPoint(0, 0))
        bubble_x = parent_pos.x() + (widget.width() - self.width()) // 2
        bubble_y = parent_pos.y() - self.height() - offset_y
        self.move(bubble_x, bubble_y)
