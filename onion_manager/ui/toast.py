from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from collections import deque


class ToastNotification(QFrame):
    _queue = deque()
    _current_toast = None

    def __init__(self, parent=None, message="", duration=4000, is_error=False):
        super().__init__(parent)
        self.duration = duration
        self.setup_ui(message, is_error)

    def setup_ui(self, message, is_error):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        if is_error:
            bg_color = "#8b0000"
            border_color = "#ff4444"
            icon = "❌"
        else:
            bg_color = "#2d6a4f"
            border_color = "#40916c"
            icon = "✅"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 10px;
                padding: 10px;
            }}
            QLabel {{
                color: white;
                font-size: 13px;
                font-weight: bold;
                background-color: transparent;
            }}
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon_label)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        self.setLayout(layout)
        self.adjustSize()
        self.position_toast()

    def position_toast(self):
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.right() - self.width() - 20
            y = parent_rect.bottom() - self.height() - 20
            self.move(x, y)

    @classmethod
    def show_toast(cls, parent, message, is_error=False):
        toast = cls(parent, message, duration=4000, is_error=is_error)
        cls._queue.append(toast)
        cls._process_queue()

    @classmethod
    def _process_queue(cls):
        if cls._current_toast is not None:
            return
        if not cls._queue:
            return
        cls._current_toast = cls._queue.popleft()
        cls._current_toast.show()
        cls._current_toast.raise_()
        QTimer.singleShot(cls._current_toast.duration, cls._close_current)

    @classmethod
{