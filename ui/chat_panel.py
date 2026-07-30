"""简易对话面板。"""

from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ChatPanel(QWidget):
    message_submitted = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, character_name: str = "洛茜", accent: str = "#C23B3B", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"和{character_name}聊天")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.resize(340, 420)
        self.setStyleSheet(
            f"""
            QWidget {{ background: #fff8f5; color: #3a2a2a; font-family: 'Microsoft YaHei'; }}
            QTextEdit {{ background: #ffffff; border: 1px solid #e8cfc8; border-radius: 8px; padding: 8px; }}
            QLineEdit {{ background: #ffffff; border: 1px solid #e8cfc8; border-radius: 8px; padding: 8px; }}
            QPushButton {{ background: {accent}; color: white; border: none; border-radius: 8px; padding: 8px 14px; }}
            QPushButton:hover {{ background: #a32f34; }}
            QPushButton:disabled {{ background: #c9a8a8; }}
            """
        )

        self._title = QLabel(f"✦ {character_name}")
        self._title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {accent};")

        self._log = QTextEdit()
        self._log.setReadOnly(True)

        self._input = QLineEdit()
        self._input.setPlaceholderText("跟她说点什么…（Enter 发送）")
        self._input.returnPressed.connect(self._submit)

        self._send = QPushButton("发送")
        self._send.clicked.connect(self._submit)

        row = QHBoxLayout()
        row.addWidget(self._input)
        row.addWidget(self._send)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._log, stretch=1)
        layout.addLayout(row)

    def set_character(self, name: str, accent: str = "#C23B3B") -> None:
        self._title.setText(f"✦ {name}")
        self.setWindowTitle(f"和{name}聊天")

    def append_user(self, text: str) -> None:
        self._log.append(f"<b>你：</b> {text}")

    def append_pet(self, name: str, text: str) -> None:
        self._log.append(f"<b style='color:#C23B3B'>{name}：</b> {text}")

    def set_busy(self, busy: bool) -> None:
        self._send.setDisabled(busy)
        self._input.setDisabled(busy)

    def _submit(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self.message_submitted.emit(text)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.closed.emit()
        super().closeEvent(event)
