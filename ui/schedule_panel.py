"""日程与健康提醒面板。"""

from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.schedule_service import ScheduleService


class SchedulePanel(QWidget):
    closed = pyqtSignal()

    def __init__(self, service: ScheduleService, accent: str = "#C23B3B", parent=None) -> None:
        super().__init__(parent)
        self._service = service
        self.setWindowTitle("日程 · 别偷懒")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(380, 520)
        self.setStyleSheet(
            f"""
            QWidget {{ background:#fff8f5; color:#3a2a2a; font-family:'Microsoft YaHei'; }}
            QLineEdit, QListWidget, QSpinBox {{ background:#fff; border:1px solid #e8cfc8; border-radius:8px; padding:4px; }}
            QPushButton {{ background:{accent}; color:white; border:none; border-radius:8px; padding:7px 12px; }}
            """
        )

        self._list = QListWidget()
        self._title = QLineEdit()
        self._title.setPlaceholderText("标题，如：开会")
        self._when = QLineEdit("15:00")
        self._when.setPlaceholderText("daily: HH:MM 或 interval: 分钟数")
        self._msg = QLineEdit()
        self._msg.setPlaceholderText("提醒台词（可空）")
        self._kind_daily = QCheckBox("每日定点（取消则为间隔分钟）")
        self._kind_daily.setChecked(True)

        add_btn = QPushButton("添加提醒")
        add_btn.clicked.connect(self._add)
        del_btn = QPushButton("删除选中")
        del_btn.clicked.connect(self._delete)

        self._health_on = QCheckBox("开启健康提醒（喝水/护眼/休息）")
        self._health_on.setChecked(service.health.enabled)
        self._water = QSpinBox()
        self._water.setRange(5, 240)
        self._water.setValue(service.health.water_min)
        self._eye = QSpinBox()
        self._eye.setRange(5, 240)
        self._eye.setValue(service.health.eye_min)
        self._rest = QSpinBox()
        self._rest.setRange(5, 360)
        self._rest.setValue(service.health.rest_min)
        save_h = QPushButton("保存健康设置")
        save_h.clicked.connect(self._save_health)

        form = QFormLayout()
        form.addRow("标题", self._title)
        form.addRow("时间", self._when)
        form.addRow("台词", self._msg)

        hform = QFormLayout()
        hform.addRow("喝水间隔(分)", self._water)
        hform.addRow("护眼间隔(分)", self._eye)
        hform.addRow("休息间隔(分)", self._rest)

        row = QHBoxLayout()
        row.addWidget(add_btn)
        row.addWidget(del_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("✦ 日程列表（可勾选启用）"))
        layout.addWidget(self._list, stretch=1)
        layout.addWidget(self._kind_daily)
        layout.addLayout(form)
        layout.addLayout(row)
        layout.addWidget(QLabel("—— 健康提醒 ——"))
        layout.addWidget(self._health_on)
        layout.addLayout(hform)
        layout.addWidget(save_h)

        self._list.itemChanged.connect(self._toggle)
        self.refresh()

    def refresh(self) -> None:
        self._list.blockSignals(True)
        self._list.clear()
        for item in self._service.items:
            label = f"{'[开]' if item.enabled else '[关]'} {item.title} · {item.kind} {item.when}"
            row = QListWidgetItem(label)
            row.setData(Qt.ItemDataRole.UserRole, item.id)
            row.setFlags(row.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            row.setCheckState(Qt.CheckState.Checked if item.enabled else Qt.CheckState.Unchecked)
            self._list.addItem(row)
        self._list.blockSignals(False)

    def _add(self) -> None:
        title = self._title.text().strip() or "提醒"
        when = self._when.text().strip() or "12:00"
        kind = "daily" if self._kind_daily.isChecked() else "interval"
        self._service.add_item(title, kind, when, self._msg.text().strip())
        self._title.clear()
        self._msg.clear()
        self.refresh()

    def _delete(self) -> None:
        cur = self._list.currentItem()
        if cur is None:
            return
        self._service.remove_item(cur.data(Qt.ItemDataRole.UserRole))
        self.refresh()

    def _toggle(self, item: QListWidgetItem) -> None:
        enabled = item.checkState() == Qt.CheckState.Checked
        self._service.toggle_item(item.data(Qt.ItemDataRole.UserRole), enabled)
        self.refresh()

    def _save_health(self) -> None:
        self._service.update_health(
            enabled=self._health_on.isChecked(),
            water_min=self._water.value(),
            eye_min=self._eye.value(),
            rest_min=self._rest.value(),
        )

    def closeEvent(self, event) -> None:  # noqa: N802
        self.closed.emit()
        super().closeEvent(event)
