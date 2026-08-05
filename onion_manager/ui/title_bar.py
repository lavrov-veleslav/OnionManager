from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QMenu
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from onion_manager.i18n.manager import lang_mgr
from onion_manager import config


class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(44)
        self.setStyleSheet("background-color: #1e1e1e;")

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        self.icon_label = QLabel()
        if config.ICON_PATH and False:
            # Optional: load icon if desired
            self.icon_label.setPixmap(QIcon(config.ICON_PATH).pixmap(20, 20))
        layout.addWidget(self.icon_label)

        self.title_label = QLabel(lang_mgr.tr("window_title"))
        self.title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # single language button
        self.lang_btn = QPushButton("���")
        self.lang_btn.setFixedSize(32, 32)
        self.lang_btn.setStyleSheet("background-color: #5a5a5a; color: white; font-size: 16px; border-radius: 4px;")
        self.lang_menu = QMenu()
        self.lang_menu.addAction(lang_mgr.tr("russian"), lambda: self.parent.change_language("ru"))
        self.lang_menu.addAction(lang_mgr.tr("english"), lambda: self.parent.change_language("en"))
        self.lang_btn.setMenu(self.lang_menu)
        layout.addWidget(self.lang_btn)

        # window control buttons
        self.min_btn = QPushButton("-")
        self.min_btn.setFixedSize(40, 32)
        self.min_btn.clicked.connect(self.parent.showMinimized)
        layout.addWidget(self.min_btn)

{