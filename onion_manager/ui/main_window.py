from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QGroupBox, QTabWidget, QPlainTextEdit, QSizePolicy
from PyQt5.QtCore import Qt
from onion_manager.i18n.manager import lang_mgr
from onion_manager.ui.title_bar import TitleBar
from onion_manager.ui.toast import ToastNotification
from onion_manager.core.tor_process import TorProcess
from onion_manager.core.bridges import load_bridges, save_bridges, get_active_bridge
from onion_manager.core.torrc import fix_paths_in_torrc, create_default_torrc, get_ports_info
from onion_manager import config


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 950, 700)

        self.tor = TorProcess(config.TOR_EXE, config.TORRC)
        self.tor.log_line.connect(self.add_log)
        self.tor.started.connect(self.on_started)
        self.tor.stopped.connect(self.on_stopped)
        self.tor.error.connect(self.on_error)

        self.init_ui()
        # apply path fixes
        try:
            fix_paths_in_torrc()
        except Exception:
            pass

    def change_language(self, lang):
        if lang_mgr.set_language(lang):
            self.refresh_ui_texts()

    def refresh_ui_texts(self):
        self.setWindowTitle(lang_mgr.tr("window_title"))
        self.title_bar.title_label.setText(lang_mgr.tr("window_title"))
        self.title_label.setText(lang_mgr.tr("title_label"))
        self.start_btn.setText(lang_mgr.tr("start_btn"))
        self.stop_btn.setText(lang_mgr.tr("stop_btn"))
{