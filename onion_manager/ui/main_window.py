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

        # initialize tor process
        self.tor = TorProcess(config.TOR_EXE, config.TORRC)
        # connect signals safely (add_log exists below)
        try:
            self.tor.log_line.connect(self.add_log)
        except Exception:
            # If tor doesn't expose log_line yet, ignore; connection may be set later
            pass
        try:
            self.tor.started.connect(self.on_started)
            self.tor.stopped.connect(self.on_stopped)
            self.tor.error.connect(self.on_error)
        except Exception:
            pass

        self.init_ui()
        # apply path fixes
        try:
            fix_paths_in_torrc()
        except Exception:
            pass

    def init_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # title bar
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        # header with title and controls
        header = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(12, 12, 12, 12)
        self.title_label = QLabel(lang_mgr.tr("title_label"))
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.start_btn = QPushButton(lang_mgr.tr("start_btn"))
        self.start_btn.clicked.connect(self.start_tor)
        header_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton(lang_mgr.tr("stop_btn"))
        self.stop_btn.clicked.connect(self.stop_tor)
        header_layout.addWidget(self.stop_btn)

        header.setLayout(header_layout)
        main_layout.addWidget(header)

        # log view
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.log_view)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # initial UI state
        self.on_stopped()

    def change_language(self, lang):
        if lang_mgr.set_language(lang):
            self.refresh_ui_texts()

    def refresh_ui_texts(self):
        # update translatable texts; guard attributes in case UI not fully initialised
        try:
            self.setWindowTitle(lang_mgr.tr("window_title"))
        except Exception:
            pass
        try:
            if hasattr(self, "title_bar") and getattr(self.title_bar, "title_label", None):
                self.title_bar.title_label.setText(lang_mgr.tr("window_title"))
        except Exception:
            pass
        try:
            if hasattr(self, "title_label"):
                self.title_label.setText(lang_mgr.tr("title_label"))
        except Exception:
            pass
        try:
            if hasattr(self, "start_btn"):
                self.start_btn.setText(lang_mgr.tr("start_btn"))
        except Exception:
            pass
        try:
            if hasattr(self, "stop_btn"):
                self.stop_btn.setText(lang_mgr.tr("stop_btn"))
        except Exception:
            pass

    def add_log(self, line: str):
        # append log line to the view; safe no-op if view not ready
        try:
            if hasattr(self, "log_view") and line is not None:
                # ensure string
                self.log_view.appendPlainText(str(line))
        except Exception:
            pass

    def start_tor(self):
        try:
            if hasattr(self.tor, "start"):
                self.tor.start()
            else:
                self.add_log("Tor start not available")
        except Exception as e:
            self.add_log(f"Error starting Tor: {e}")

    def stop_tor(self):
        try:
            if hasattr(self.tor, "stop"):
                self.tor.stop()
            else:
                self.add_log("Tor stop not available")
        except Exception as e:
            self.add_log(f"Error stopping Tor: {e}")

    def on_started(self):
        try:
            if hasattr(self, "start_btn"):
                self.start_btn.setEnabled(False)
            if hasattr(self, "stop_btn"):
                self.stop_btn.setEnabled(True)
            self.add_log("Tor started")
        except Exception:
            pass

    def on_stopped(self):
        try:
            if hasattr(self, "start_btn"):
                self.start_btn.setEnabled(True)
            if hasattr(self, "stop_btn"):
                self.stop_btn.setEnabled(False)
            self.add_log("Tor stopped")
        except Exception:
            pass

    def on_error(self, err_msg=None):
        try:
            self.add_log(f"Tor error: {err_msg}")
            # show toast notification if available
            try:
                ToastNotification.show_toast(self, f"Tor error: {err_msg}", is_error=True)
            except Exception:
                pass
        except Exception:
            pass
