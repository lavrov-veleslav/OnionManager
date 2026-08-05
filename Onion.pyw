#!/usr/bin/env python3
"""
Standalone Onion.pyw
This single-file launcher includes minimal core helpers (config, bridges, tor process,
language manager) and the full UI (TitleBar, ToastNotification, MainWindow) so it can
run without importing the modular package.

Usage: place this file alongside the `tor/` folder and `data/` directory as described
in README, then double-click or run `python Onion.pyw`.
"""

import os
import sys
import json
import re
from collections import deque

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
        QLabel, QGroupBox, QTabWidget, QPlainTextEdit, QSizePolicy, QSplitter, QFrame, QMenu
    )
    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal, QProcess
except Exception as e:
    raise RuntimeError("PyQt5 is required to run Onion.pyw: " + str(e))

# --- Minimal config (like onion_manager/config.py) ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TOR_EXE = os.path.join(BASE_DIR, 'tor', 'tor.exe')
TORRC = os.path.join(BASE_DIR, 'data', 'torrc')
BRIDGE_FILE = os.path.join(BASE_DIR, 'data', 'bridge')
ICON_PATH = os.path.join(BASE_DIR, 'icon.ico')
LANG_PATHS = [
    os.path.join(BASE_DIR, 'onion_manager', 'i18n', 'lang.json'),
    os.path.join(BASE_DIR, 'lang.json')
]

# --- Minimal language manager ---
class LangManager:
    def __init__(self):
        self.lang = 'ru'
        self.strings = {}
        self._load()

    def _load(self):
        for p in LANG_PATHS:
            if os.path.exists(p):
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        self.strings = json.load(f)
                    return
                except Exception:
                    continue
        # fallback minimal English strings
        self.strings = {
            'en': {
                'window_title': 'Onion Manager',
                'tab_logs': 'Logs',
                'tab_bridges': 'Bridges',
                'load_bridge_btn': 'Load',
                'save_bridge_btn': 'Save',
                'clear_logs_btn': 'Clear logs',
                'bridges_file': 'Bridges file',
                'info_panel': 'System Information',
                'tor_exe': 'Tor executable:',
                'tor_config': 'Tor config:',
                'bridges_file': 'Bridges file:',
                'ports_info': 'Ports:',
                'ports_not_found': 'Ports not found',
                'bridge_file_not_found': 'Bridges file not found',
                'bridges_loaded': 'Bridges loaded',
                'bridges_saved': 'Bridges saved',
                'logs_cleared': 'Logs cleared',
                'active_bridge': 'Active bridge',
                'not_found': '(not found)',
                'tor_started': 'Tor started (PID: ',
                'tor_stopped': 'Tor stopped'
            }
        }

    def set_language(self, lang_code: str) -> bool:
        if lang_code in self.strings:
            self.lang = lang_code
            return True
        return False

    def tr(self, key: str) -> str:
        try:
            return self.strings.get(self.lang, {}).get(key, self.strings.get('en', {}).get(key, key))
        except Exception:
            return key

lang_mgr = LangManager()

# --- Bridges helpers (copied/adapted) ---

def load_bridges(path: str):
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.splitlines()
        cleaned = []
        for line in lines:
            s = line.strip()
            if s.lower().startswith('bridge '):
                cleaned.append(s[7:].lstrip())
            else:
                cleaned.append(line)
        return '\n'.join(cleaned).rstrip('\n')
    except Exception:
        return None


def save_bridges(path: str, text: str) -> bool:
    try:
        lines = text.strip().split('\n')
        formatted = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                formatted.append(line)
            else:
                formatted.append(f"bridge {line}")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # backup
        try:
            if os.path.exists(path):
                import shutil
                shutil.copy2(path, path + '.bak')
        except Exception:
            pass
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(formatted))
        return True
    except Exception:
        return False


def _find_ip_port_in_line(line: str):
    m = re.search(r"(?:(?:\d{1,3}\.){3}\d{1,3}):(\d{1,5})", line)
    if not m:
        return None
    ip_port = m.group(0)
    ip, port = ip_port.split(':')
    octets = ip.split('.')
    try:
        if len(octets) != 4:
            return None
        for o in octets:
            if not 0 <= int(o) <= 255:
                return None
        p = int(port)
        if not 0 < p <= 65535:
            return None
    except Exception:
        return None
    return ip_port


def get_active_bridge(path: str):
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                if line.lower().startswith('bridge '):
                    line_to_check = line[7:].lstrip()
                else:
                    line_to_check = line
                found = _find_ip_port_in_line(line_to_check)
                if found:
                    return found
        return None
    except Exception:
        return None

# --- Minimal TorProcess wrapper using QProcess ---
class TorProcess(QObject):
    log_line = pyqtSignal(object, object)  # (level, text) or (text,)
    started = pyqtSignal(object)
    stopped = pyqtSignal(object)
    error = pyqtSignal(object)

    def __init__(self, tor_path: str, torrc: str):
        super().__init__()
        self.tor_path = tor_path
        self.torrc = torrc
        self.proc = QProcess(self)
        try:
            self.proc.readyReadStandardOutput.connect(self._on_stdout)
        except Exception:
            pass
        try:
            self.proc.started.connect(self._on_started)
            self.proc.finished.connect(self._on_finished)
            self.proc.errorOccurred.connect(self._on_error)
        except Exception:
            pass

    def start(self):
        if not self.tor_path or not os.path.exists(self.tor_path):
            self.error.emit('Tor executable not found')
            return False
        try:
            args = ['-f', self.torrc]
            self.proc.start(self.tor_path, args)
            return True
        except Exception as e:
            self.error.emit(str(e))
            return False

    def stop(self):
        try:
            if self.proc.state() != QProcess.NotRunning:
                self.proc.terminate()
        except Exception:
            pass

    def _on_started(self):
        try:
            pid = int(self.proc.processId()) if hasattr(self.proc, 'processId') else None
            self.started.emit(pid)
        except Exception:
            self.started.emit(None)

    def _on_stdout(self):
        try:
            data = bytes(self.proc.readAllStandardOutput()).decode('utf-8', errors='ignore')
            for line in data.splitlines():
                lvl = 'info'
                l = line.lower()
                if '[warn]' in l:
                    lvl = 'warn'
                if '[err]' in l or '[error]' in l:
                    lvl = 'error'
                self.log_line.emit(lvl, line)
        except Exception:
            pass

    def _on_finished(self, exit_code, exit_status):
        try:
            self.stopped.emit(exit_code)
        except Exception:
            self.stopped.emit(None)

    def _on_error(self, error):
        try:
            self.error.emit(str(error))
        except Exception:
            self.error.emit('unknown error')

# --- UI components (TitleBar & Toast embedded) ---
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
    def show_toast(cls, parent, message, is_error=False, duration=4000):
        toast = cls(parent, message, duration=duration, is_error=is_error)
        cls._queue.append(toast)
        cls._process_queue()

    @classmethod
    def _process_queue(cls):
        if cls._current_toast is not None:
            return
        if not cls._queue:
            return
        cls._current_toast = cls._queue.popleft()
        try:
            cls._current_toast.show()
            cls._current_toast.raise_()
            QTimer.singleShot(cls._current_toast.duration, cls._close_current)
        except Exception:
            cls._current_toast = None
            QTimer.singleShot(0, cls._process_queue)

    @classmethod
    def _close_current(cls):
        try:
            if cls._current_toast is not None:
                try:
                    cls._current_toast.hide()
                    cls._current_toast.deleteLater()
                except Exception:
                    pass
                cls._current_toast = None
        finally:
            QTimer.singleShot(0, cls._process_queue)


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
        if os.path.exists(ICON_PATH):
            try:
                self.icon_label.setPixmap(QIcon(ICON_PATH).pixmap(20, 20))
            except Exception:
                pass
        layout.addWidget(self.icon_label)
        self.title_label = QLabel(lang_mgr.tr("window_title"))
        self.title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.title_label)
        layout.addStretch()
        self.lang_btn = QPushButton("🌐")
        self.lang_btn.setFixedSize(32, 32)
        self.lang_btn.setStyleSheet("background-color: #5a5a5a; color: white; font-size: 16px; border-radius: 4px;")
        self.lang_menu = QMenu()
        try:
            self.lang_menu.addAction(lang_mgr.tr("russian"), lambda: self.parent.change_language("ru") if self.parent else None)
            self.lang_menu.addAction(lang_mgr.tr("english"), lambda: self.parent.change_language("en") if self.parent else None)
        except Exception:
            pass
        self.lang_btn.setMenu(self.lang_menu)
        layout.addWidget(self.lang_btn)
        self.min_btn = QPushButton("-")
        self.min_btn.setFixedSize(40, 32)
        if self.parent:
            try:
                self.min_btn.clicked.connect(self.parent.showMinimized)
            except Exception:
                pass
        layout.addWidget(self.min_btn)
        self.close_btn = QPushButton("x")
        self.close_btn.setFixedSize(40, 32)
        self.close_btn.setStyleSheet("background-color: #e81123; color: white; font-weight: bold;")
        if self.parent:
            try:
                self.close_btn.clicked.connect(self.parent.close)
            except Exception:
                pass
        layout.addWidget(self.close_btn)
        self.setLayout(layout)


# --- Main window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 950, 700)

        self.tor = TorProcess(TOR_EXE, TORRC)
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

        self.init_ui()
        try:
            fix_paths_in_torrc(TORRC)
        except Exception:
            pass

    def init_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        splitter = QSplitter(Qt.Horizontal)

        # Left: tabs
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(8, 8, 8, 8)

        self.tabs = QTabWidget()
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.tabs.addTab(self.log_view, lang_mgr.tr("tab_logs"))

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

        # Right: info
        info_widget = QGroupBox(lang_mgr.tr("info_panel"))
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(8, 8, 8, 8)
        self.tor_exe_label = QLabel(f"{lang_mgr.tr('tor_exe')} {TOR_EXE}")
        info_layout.addWidget(self.tor_exe_label)
        self.torrc_label = QLabel(f"{lang_mgr.tr('tor_config')} {TORRC}")
        info_layout.addWidget(self.torrc_label)
        self.bridges_file_label = QLabel(f"{lang_mgr.tr('bridges_file')} {BRIDGE_FILE}")
        info_layout.addWidget(self.bridges_file_label)
        try:
            ports_info = get_ports_info(TORRC)
        except Exception:
            ports_info = None
        self.ports_label = QLabel(f"{lang_mgr.tr('ports_info')} {ports_info if ports_info else lang_mgr.tr('ports_not_found')}")
        info_layout.addWidget(self.ports_label)
        info_layout.addStretch()
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

        self.on_stopped()
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
            self.bridges_file_label.setText(f"{lang_mgr.tr('bridges_file')} {BRIDGE_FILE}")
            self.tor_exe_label.setText(f"{lang_mgr.tr('tor_exe')} {TOR_EXE}")
            self.torrc_label.setText(f"{lang_mgr.tr('tor_config')} {TORRC}")
            self.ports_label.setText(f"{lang_mgr.tr('ports_info')} {get_ports_info(TORRC) if get_ports_info else lang_mgr.tr('ports_not_found')}")
        except Exception:
            pass
        self.refresh_active_bridge()

    def add_log(self, level, text=None):
        try:
            if text is None:
                text = level
                level = 'info'
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
            content = load_bridges_file(BRIDGE_FILE)
            if content is None:
                ToastNotification.show_toast(self, f"{lang_mgr.tr('bridge_file_not_found')} {BRIDGE_FILE}", is_error=True)
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
            ok = save_bridges_file(BRIDGE_FILE, text)
            if ok:
                ToastNotification.show_toast(self, lang_mgr.tr('bridges_saved'))
            else:
                ToastNotification.show_toast(self, lang_mgr.tr('error_saving_bridges'), is_error=True)
            self.refresh_active_bridge()
        except Exception as e:
            ToastNotification.show_toast(self, f"{lang_mgr.tr('error_saving_bridges')} {e}", is_error=True)

    def refresh_active_bridge(self):
        try:
            ab = get_active_bridge(BRIDGE_FILE)
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


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Onion Manager')
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
