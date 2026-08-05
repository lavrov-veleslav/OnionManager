from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QTabWidget, QPlainTextEdit, QSizePolicy, QSplitter
)
from PyQt5.QtCore import Qt
from onion_manager.i18n.manager import lang_mgr
from onion_manager.ui.title_bar import TitleBar
from onion_manager.ui.toast import ToastNotification
from onion_manager.core.tor_process import TorProcess
from onion_manager.core.bridges import load_bridges as load_bridges_file, save_bridges as save_bridges_file, get_active_bridge
from onion_manager.core.torrc import fix_paths_in_torrc, create_default_torrc, get_ports_info
from onion_manager import config


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 950, 700)

        # Tor process
        self.tor = TorProcess(config.TOR_EXE, config.TORRC)
        try:
            self.tor.log_line.connect(self.add_log)
        except Exception:
            pass
        try:
            self.tor.started.connect(self.on_started)
            self.tor.stopped.connect(self.on_stopped)
            self.tor.error.connect(self.on_error)
        except Exception:
            pass

        # build UI
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

        # Title bar
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Main splitter: left - tabs, right - info
        splitter = QSplitter(Qt.Horizontal)

        # Left side: tabs
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(8, 8, 8, 8)

        self.tabs = QTabWidget()
        # Logs tab
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.tabs.addTab(self.log_view, lang_mgr.tr("tab_logs"))

        # Bridges tab
        bridges_widget = QWidget()
        bridges_layout = QVBoxLayout()
        bridges_layout.setContentsMargins(8, 8, 8, 8)

        self.bridges_edit = QPlainTextEdit()
        self.bridges_edit.setPlaceholderText(lang_mgr.tr("bridges_file") + "...")
        bridges_layout.addWidget(self.bridges_edit)

        btn_row = QHBoxLayout()
        self.load_bridge_btn = QPushButton(lang_mgr.tr("load_bridge_btn"))
        self.load_bridge_btn.clicked.connect(self.load_bridges_ui)
        btn_row.addWidget(self.load_bridge_btn)

        self.save_bridge_btn = QPushButton(lang_mgr.tr("save_bridge_btn"))
        self.save_bridge_btn.clicked.connect(self.save_bridges_ui)
        btn_row.addWidget(self.save_bridge_btn)

        btn_row.addStretch()

        self.clear_logs_btn = QPushButton(lang_mgr.tr("clear_logs_btn"))
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        btn_row.addWidget(self.clear_logs_btn)

        bridges_layout.addLayout(btn_row)
        bridges_widget.setLayout(bridges_layout)
        self.tabs.addTab(bridges_widget, lang_mgr.tr("tab_bridges"))

        left_layout.addWidget(self.tabs)
        left_widget.setLayout(left_layout)

        splitter.addWidget(left_widget)

        # Right side: info panel
        info_widget = QGroupBox(lang_mgr.tr("info_panel"))
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(8, 8, 8, 8)

        self.tor_exe_label = QLabel(f"{lang_mgr.tr('tor_exe')} {config.TOR_EXE}")
        info_layout.addWidget(self.tor_exe_label)

        self.torrc_label = QLabel(f"{lang_mgr.tr('tor_config')} {config.TORRC}")
        info_layout.addWidget(self.torrc_label)

        self.bridges_file_label = QLabel(f"{lang_mgr.tr('bridges_file')} {config.BRIDGE_FILE}")
        info_layout.addWidget(self.bridges_file_label)

        # ports info (best-effort)
        try:
            ports_info = get_ports_info(config.TORRC)
        except Exception:
            ports_info = None
        self.ports_label = QLabel(f"{lang_mgr.tr('ports_info')} {ports_info if ports_info else lang_mgr.tr('ports_not_found')}")
        info_layout.addWidget(self.ports_label)

        info_layout.addStretch()

        # Active bridge display (bottom-right in info area)
        self.active_bridge_label = QLabel()
        self.refresh_active_bridge()
        info_layout.addWidget(self.active_bridge_label, alignment=Qt.AlignRight)

        info_widget.setLayout(info_layout)
        info_widget.setMaximumWidth(320)
        splitter.addWidget(info_widget)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # initial UI state
        self.on_stopped()

        # Try to load bridges into editor on startup
        try:
            self.load_bridges_ui()
        except Exception:
            pass

    def change_language(self, lang):
        if lang_mgr.set_language(lang):
            self.refresh_ui_texts()

    def refresh_ui_texts(self):
        try:
            self.setWindowTitle(lang_mgr.tr("window_title"))
        except Exception:
            pass
        try:
            self.title_bar.title_label.setText(lang_mgr.tr("window_title"))
        except Exception:
            pass
        try:
            self.tabs.setTabText(0, lang_mgr.tr("tab_logs"))
            self.tabs.setTabText(1, lang_mgr.tr("tab_bridges"))
        except Exception:
            pass
        try:
            self.load_bridge_btn.setText(lang_mgr.tr("load_bridge_btn"))
            self.save_bridge_btn.setText(lang_mgr.tr("save_bridge_btn"))
            self.clear_logs_btn.setText(lang_mgr.tr("clear_logs_btn"))
        except Exception:
            pass
        try:
            self.bridges_edit.setPlaceholderText(lang_mgr.tr("bridges_file") + "...")
        except Exception:
            pass
        try:
            self.bridges_file_label.setText(f"{lang_mgr.tr('bridges_file')} {config.BRIDGE_FILE}")
            self.tor_exe_label.setText(f"{lang_mgr.tr('tor_exe')} {config.TOR_EXE}")
            self.torrc_label.setText(f"{lang_mgr.tr('tor_config')} {config.TORRC}")
            self.ports_label.setText(f"{lang_mgr.tr('ports_info')} {get_ports_info(config.TORRC) if get_ports_info else lang_mgr.tr('ports_not_found')}")
        except Exception:
            pass
        self.refresh_active_bridge()

    def add_log(self, *args):
        # tor.log_line may emit (level, text) or just a single message depending on implementation
        try:
            if len(args) == 2:
                level, text = args
            elif len(args) == 1:
                text = args[0]
                level = 'info'
            else:
                return
            line = f"[{level.upper()}] {text}"
            if hasattr(self, 'log_view'):
                self.log_view.appendPlainText(line)
        except Exception:
            pass

    def clear_logs(self):
        try:
            if hasattr(self, 'log_view'):
                self.log_view.clear()
                ToastNotification.show_toast(self, lang_mgr.tr('logs_cleared'))
        except Exception:
            pass

    def load_bridges_ui(self):
        try:
            content = load_bridges_file(config.BRIDGE_FILE)
            if content is None:
                ToastNotification.show_toast(self, f"{lang_mgr.tr('bridge_file_not_found')} {config.BRIDGE_FILE}", is_error=True)
                self.bridges_edit.setPlainText("")
            else:
                self.bridges_edit.setPlainText(content)
                ToastNotification.show_toast(self, lang_mgr.tr('bridges_loaded'))
            self.refresh_active_bridge()
        except Exception as e:
            ToastNotification.show_toast(self, f"{lang_mgr.tr('error_loading_bridges')} {e}", is_error=True)

    def save_bridges_ui(self):
        try:
            text = self.bridges_edit.toPlainText()
            ok = save_bridges_file(config.BRIDGE_FILE, text)
            if ok:
                ToastNotification.show_toast(self, lang_mgr.tr('bridges_saved'))
            else:
                ToastNotification.show_toast(self, lang_mgr.tr('error_saving_bridges'), is_error=True)
            self.refresh_active_bridge()
        except Exception as e:
            ToastNotification.show_toast(self, f"{lang_mgr.tr('error_saving_bridges')} {e}", is_error=True)

    def refresh_active_bridge(self):
        try:
            ab = get_active_bridge(config.BRIDGE_FILE)
            if ab:
                text = f"{lang_mgr.tr('active_bridge')}: {ab}"
            else:
                text = f"{lang_mgr.tr('active_bridge')}: {lang_mgr.tr('not_found') if hasattr(lang_mgr, 'tr') else '(not found)'}"
            if hasattr(self, 'active_bridge_label'):
                self.active_bridge_label.setText(text)
        except Exception:
            pass

    def start_tor(self):
        try:
            if hasattr(self.tor, 'start'):
                self.tor.start()
            else:
                ToastNotification.show_toast(self, 'Tor start not available', is_error=True)
        except Exception as e:
            ToastNotification.show_toast(self, f"Error starting Tor: {e}", is_error=True)

    def stop_tor(self):
        try:
            if hasattr(self.tor, 'stop'):
                self.tor.stop()
            else:
                ToastNotification.show_toast(self, 'Tor stop not available', is_error=True)
        except Exception as e:
            ToastNotification.show_toast(self, f"Error stopping Tor: {e}", is_error=True)

    def on_started(self, *args):
        try:
            ToastNotification.show_toast(self, lang_mgr.tr('tor_started') + (str(args[0]) if args else ''))
            if hasattr(self, 'start_btn'):
                self.start_btn.setEnabled(False)
            if hasattr(self, 'stop_btn'):
                self.stop_btn.setEnabled(True)
        except Exception:
            pass

    def on_stopped(self, *args):
        try:
            ToastNotification.show_toast(self, lang_mgr.tr('tor_stopped'))
            if hasattr(self, 'start_btn'):
                self.start_btn.setEnabled(True)
            if hasattr(self, 'stop_btn'):
                self.stop_btn.setEnabled(False)
        except Exception:
            pass

    def on_error(self, err_msg=None):
        try:
            ToastNotification.show_toast(self, f"Tor error: {err_msg}", is_error=True)
        except Exception:
            pass
