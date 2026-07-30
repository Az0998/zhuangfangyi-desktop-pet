"""剪贴板历史面板。"""

from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.clipboard_service import ClipboardItem, ClipboardService


class ClipboardPanel(QWidget):
    restore_requested = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, service: ClipboardService, accent: str = "#C23B3B", parent=None) -> None:
        super().__init__(parent)
        self._service = service
        self.setWindowTitle("剪贴板 · 洛茜帮你记着")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(360, 460)
        self.setStyleSheet(
            f"""
            QWidget {{ background:#fff8f5; color:#3a2a2a; font-family:'Microsoft YaHei'; }}
            QLineEdit, QListWidget {{ background:#fff; border:1px solid #e8cfc8; border-radius:8px; }}
            QPushButton {{ background:{accent}; color:white; border:none; border-radius:8px; padding:7px 12px; }}
            QPushButton:hover {{ background:#a32f34; }}
            """
        )

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索复制过的内容…")
        self._search.textChanged.connect(self.refresh)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._on_double)

        btn_restore = QPushButton("粘回剪贴板")
        btn_restore.clicked.connect(self._restore_selected)
        btn_clear = QPushButton("清空历史")
        btn_clear.clicked.connect(self._clear)
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.refresh)

        row = QHBoxLayout()
        row.addWidget(btn_restore)
        row.addWidget(btn_refresh)
        row.addWidget(btn_clear)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("✦ 剪贴板历史（双击亦可粘回）"))
        layout.addWidget(self._search)
        layout.addWidget(self._list, stretch=1)
        layout.addLayout(row)
        self.refresh()

    def refresh(self) -> None:
        self._list.clear()
        for item in reversed(self._service.search(self._search.text())):
            label = f"[{item.kind}] {item.preview}"
            row = QListWidgetItem(label)
            row.setData(Qt.ItemDataRole.UserRole, item.text)
            self._list.addItem(row)

    def _restore_selected(self) -> None:
        cur = self._list.currentItem()
        if cur is None:
            return
        text = cur.data(Qt.ItemDataRole.UserRole)
        self._service.restore(text)
        self.restore_requested.emit(text)

    def _on_double(self, item: QListWidgetItem) -> None:
        text = item.data(Qt.ItemDataRole.UserRole)
        self._service.restore(text)
        self.restore_requested.emit(text)

    def _clear(self) -> None:
        self._service.clear()
        self.refresh()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.closed.emit()
        super().closeEvent(event)
