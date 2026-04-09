# pip install PyQt5

import sys
import os
import subprocess
import threading
import time
import re
import warnings
import json
from datetime import datetime
from collections import deque

warnings.filterwarnings("ignore", message="Cannot queue arguments of type 'QTextCursor'")

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                             QGroupBox, QTabWidget, QPlainTextEdit, QFrame,
                             QSizePolicy, QMenu)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QFont, QIcon

# ==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ====================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TOR_EXE = os.path.join(BASE_DIR, "tor", "tor.exe")
TORRC = os.path.join(BASE_DIR, "data", "torrc")
BRIDGE_FILE = os.path.join(BASE_DIR, "data", "bridge")
LYREBIRD_EXE = os.path.join(BASE_DIR, "tor", "pluggable_transports", "lyrebird.exe")
CONJURE_EXE = os.path.join(BASE_DIR, "tor", "pluggable_transports", "conjure-client.exe")
ICON_PATH = os.path.join(BASE_DIR, "icon.ico")
LANG_FILE = os.path.join(BASE_DIR, "lang.json")
# ============================================================

class LanguageManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_languages()
        return cls._instance
    
    def _load_languages(self):
        self.strings = {}
        self.current_lang = "ru"
        try:
            with open(LANG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.strings = data
        except Exception as e:
            print(f"Error loading lang.json: {e}")
            # Fallback hardcoded
            self.strings = {
                "ru": {"window_title": "Onion Manager", "title_label": "Onion Control Panel", "start_btn": "▶ Запустить"},
                "en": {"window_title": "Onion Manager", "title_label": "Onion Control Panel", "start_btn": "▶ Start"}
            }
    
    def tr(self, key):
        return self.strings.get(self.current_lang, {}).get(key, self.strings.get("en", {}).get(key, key))
    
    def set_language(self, lang):
        if lang in self.strings:
            self.current_lang = lang
            return True
        return False

lang_mgr = LanguageManager()

class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(44)
        self.setStyleSheet("background-color: #1e1e1e;")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)
        
        self.icon_label = QLabel()
        if os.path.exists(ICON_PATH):
            self.icon_label.setPixmap(QIcon(ICON_PATH).pixmap(20, 20))
        layout.addWidget(self.icon_label)
        
        self.title_label = QLabel(lang_mgr.tr("window_title"))
        self.title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Кнопка выбора языка
        self.lang_btn = QPushButton("🌐")
        self.lang_btn.setFixedSize(32, 32)
        self.lang_btn.setStyleSheet("background-color: #5a5a5a; color: white; font-size: 16px; border-radius: 4px;")
        self.lang_menu = QMenu()
        self.lang_menu.addAction(lang_mgr.tr("russian"), lambda: self.parent.change_language("ru"))
        self.lang_menu.addAction(lang_mgr.tr("english"), lambda: self.parent.change_language("en"))
        self.lang_btn.setMenu(self.lang_menu)
        layout.addWidget(self.lang_btn)
        
        btn_style = """
            QPushButton {
                background-color: #5a5a5a;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-family: "Consolas", "Segoe UI", monospace;
            }
        """
        
        self.min_btn = QPushButton("-")
        self.min_btn.setFixedSize(40, 32)
        self.min_btn.setStyleSheet(btn_style + " color: #ffcc00; font-size: 20px;")
        self.min_btn.clicked.connect(self.parent.showMinimized)
        
        self.max_btn = QPushButton("#")
        self.max_btn.setFixedSize(40, 32)
        self.max_btn.setStyleSheet(btn_style + " color: #ffaa00; font-size: 22px;")
        self.max_btn.clicked.connect(self.toggle_maximize)
        
        self.close_btn = QPushButton("X")
        self.close_btn.setFixedSize(40, 32)
        self.close_btn.setStyleSheet(btn_style + " color: #ff5555; font-size: 20px;")
        self.close_btn.clicked.connect(self.parent.close)
        
        layout.addWidget(self.lang_btn)
        layout.addWidget(self.min_btn)
        layout.addWidget(self.max_btn)
        layout.addWidget(self.close_btn)
        
        self.setLayout(layout)
        self.drag_pos = None
    
    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.max_btn.setText("#")
        else:
            self.parent.showMaximized()
            self.max_btn.setText("#")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            delta = event.globalPos() - self.drag_pos
            self.parent.move(self.parent.pos() + delta)
            self.drag_pos = event.globalPos()
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.drag_pos = None
        event.accept()
        
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
        else:
            screen = QApplication.primaryScreen().geometry()
            x = screen.right() - self.width() - 20
            y = screen.bottom() - self.height() - 20
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
    def _close_current(cls):
        if cls._current_toast:
            cls._current_toast.close()
            cls._current_toast = None
        cls._process_queue()
    
    def closeEvent(self, event):
        if ToastNotification._current_toast is self:
            ToastNotification._current_toast = None
        super().closeEvent(event)

class TorWorker(QObject):
    log_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.process = None
        self.running = False
        
    def start_tor(self):
        if not os.path.exists(TOR_EXE):
            self.status_signal.emit(lang_mgr.tr("error_tor_not_found") + TOR_EXE)
            return False
        
        try:
            self.process = subprocess.Popen(
                [TOR_EXE, "-f", TORRC],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            self.running = True
            self.status_signal.emit(lang_mgr.tr("tor_started") + str(self.process.pid) + ")")
            threading.Thread(target=self.read_logs, daemon=True).start()
            return True
            
        except Exception as e:
            self.status_signal.emit(f"ОШИБКА: {e}")
            return False
    
    def read_logs(self):
        while self.running and self.process and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if line:
                    line = line.strip()
                    if "[warn]" in line:
                        self.log_signal.emit(line, "warn")
                    elif "[err]" in line:
                        self.log_signal.emit(line, "error")
                    else:
                        self.log_signal.emit(line, "info")
            except:
                break
    
    def stop_tor(self):
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
                self.status_signal.emit(lang_mgr.tr("tor_stopped"))
            except:
                try:
                    self.process.kill()
                    self.status_signal.emit(lang_mgr.tr("tor_killed"))
                except:
                    pass
            self.process = None
    
    def restart_tor(self):
        self.status_signal.emit(lang_mgr.tr("restart"))
        self.stop_tor()
        time.sleep(2)
        return self.start_tor()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        
        self.worker = TorWorker()
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        
        self.worker.log_signal.connect(self.add_log)
        self.worker.status_signal.connect(self.update_status)
        
        self.thread.start()
        
        self.init_ui()
        self.is_running = False
        self.bridge_file = BRIDGE_FILE
        
        self.check_and_fix_all_paths()
        self.load_bridge_config()
        
        QTimer.singleShot(1000, self.start_tor)
    
    def change_language(self, lang):
        if lang_mgr.set_language(lang):
            self.refresh_ui_texts()
    
    def refresh_ui_texts(self):
        self.setWindowTitle(lang_mgr.tr("window_title"))
        self.title_bar.title_label.setText(lang_mgr.tr("window_title"))
        self.title_bar.lang_btn.setMenu(None)
        self.title_bar.lang_menu = QMenu()
        self.title_bar.lang_menu.addAction(lang_mgr.tr("russian"), lambda: self.change_language("ru"))
        self.title_bar.lang_menu.addAction(lang_mgr.tr("english"), lambda: self.change_language("en"))
        self.title_bar.lang_btn.setMenu(self.title_bar.lang_menu)
        
        self.title_label.setText(lang_mgr.tr("title_label"))
        self.start_btn.setText(lang_mgr.tr("start_btn"))
        self.stop_btn.setText(lang_mgr.tr("stop_btn"))
        self.restart_btn.setText(lang_mgr.tr("restart_btn"))
        self.status_label.setText(lang_mgr.tr("status_label"))
        self.tabs.setTabText(0, lang_mgr.tr("tab_logs"))
        self.tabs.setTabText(1, lang_mgr.tr("tab_warnings"))
        self.tabs.setTabText(2, lang_mgr.tr("tab_errors"))
        self.tabs.setTabText(3, lang_mgr.tr("tab_bridges"))
        self.save_bridge_btn.setText(lang_mgr.tr("save_bridge_btn"))
        self.load_bridge_btn.setText(lang_mgr.tr("load_bridge_btn"))
        self.clear_btn.setText(lang_mgr.tr("clear_logs_btn"))
        self.info_panel.setTitle(lang_mgr.tr("info_panel"))
        self.update_system_info()
    
    def init_ui(self):
        self.setGeometry(100, 100, 950, 700)
        
        central = QWidget()
        central.setObjectName("central")
        central.setStyleSheet("""
            QWidget#central {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
            }
            QTextEdit, QPlainTextEdit {
                background-color: #2d2d30;
                color: #d4d4d4;
                font-family: Consolas;
                font-size: 11px;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0a4c74;
            }
            QPushButton#stop {
                background-color: #a1260d;
            }
            QPushButton#stop:hover {
                background-color: #c42b0e;
            }
            QPushButton#restart {
                background-color: #d48c0a;
            }
            QPushButton#restart:hover {
                background-color: #f0a010;
            }
            QPushButton#save {
                background-color: #2d6a4f;
            }
            QPushButton#save:hover {
                background-color: #40916c;
            }
            QGroupBox {
                color: #d4d4d4;
                border: 2px solid #3c3c3c;
                border-radius: 8px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: #d4d4d4;
            }
            QTabWidget::pane {
                background-color: #252526;
                border: 1px solid #3c3c3c;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #d4d4d4;
                padding: 8px 15px;
            }
            QTabBar::tab:selected {
                background-color: #0e639c;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3c3c3c;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)
        
        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        title_layout.setSpacing(15)
        
        left_icon = QLabel()
        if os.path.exists(ICON_PATH):
            left_icon.setPixmap(QIcon(ICON_PATH).pixmap(32, 32))
        title_layout.addWidget(left_icon)
        
        self.title_label = QLabel(lang_mgr.tr("title_label"))
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #4ec9b0; background-color: transparent;")
        title_layout.addWidget(self.title_label)
        
        right_icon = QLabel()
        if os.path.exists(ICON_PATH):
            right_icon.setPixmap(QIcon(ICON_PATH).pixmap(32, 32))
        title_layout.addWidget(right_icon)
        
        content_layout.addLayout(title_layout)
        
        btn_group = QGroupBox(lang_mgr.tr("control"))
        btn_group.setTitle(lang_mgr.tr("control"))
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton(lang_mgr.tr("start_btn"))
        self.start_btn.clicked.connect(self.start_tor)
        self.stop_btn = QPushButton(lang_mgr.tr("stop_btn"))
        self.stop_btn.setObjectName("stop")
        self.stop_btn.clicked.connect(self.stop_tor)
        self.stop_btn.setEnabled(False)
        self.restart_btn = QPushButton(lang_mgr.tr("restart_btn"))
        self.restart_btn.setObjectName("restart")
        self.restart_btn.clicked.connect(self.restart_tor)
        self.restart_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.restart_btn)
        btn_layout.addStretch()
        btn_group.setLayout(btn_layout)
        content_layout.addWidget(btn_group)
        
        status_group = QGroupBox(lang_mgr.tr("status"))
        status_layout = QVBoxLayout()
        self.status_label = QLabel(lang_mgr.tr("status_label"))
        self.status_label.setStyleSheet("background-color: #2d2d30; padding: 8px; border-radius: 5px;")
        status_layout.addWidget(self.status_label)
        status_group.setLayout(status_layout)
        content_layout.addWidget(status_group)
        
        self.tabs = QTabWidget()
        
        log_widget = QWidget()
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_widget.setLayout(log_layout)
        self.tabs.addTab(log_widget, lang_mgr.tr("tab_logs"))
        
        warn_widget = QWidget()
        warn_layout = QVBoxLayout()
        self.warn_text = QTextEdit()
        self.warn_text.setReadOnly(True)
        warn_layout.addWidget(self.warn_text)
        warn_widget.setLayout(warn_layout)
        self.tabs.addTab(warn_widget, lang_mgr.tr("tab_warnings"))
        
        error_widget = QWidget()
        error_layout = QVBoxLayout()
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        error_layout.addWidget(self.error_text)
        error_widget.setLayout(error_layout)
        self.tabs.addTab(error_widget, lang_mgr.tr("tab_errors"))
        
        bridge_widget = QWidget()
        bridge_layout = QVBoxLayout()
        self.bridge_edit = QPlainTextEdit()
        bridge_layout.addWidget(self.bridge_edit)
        bridge_btn_layout = QHBoxLayout()
        self.save_bridge_btn = QPushButton(lang_mgr.tr("save_bridge_btn"))
        self.save_bridge_btn.setObjectName("save")
        self.save_bridge_btn.clicked.connect(self.save_bridge_config)
        self.load_bridge_btn = QPushButton(lang_mgr.tr("load_bridge_btn"))
        self.load_bridge_btn.clicked.connect(self.load_bridge_config)
        bridge_btn_layout.addWidget(self.save_bridge_btn)
        bridge_btn_layout.addWidget(self.load_bridge_btn)
        bridge_btn_layout.addStretch()
        bridge_layout.addLayout(bridge_btn_layout)
        bridge_widget.setLayout(bridge_layout)
        self.tabs.addTab(bridge_widget, lang_mgr.tr("tab_bridges"))
        
        content_layout.addWidget(self.tabs)
        
        self.clear_btn = QPushButton(lang_mgr.tr("clear_logs_btn"))
        self.clear_btn.clicked.connect(self.clear_logs)
        content_layout.addWidget(self.clear_btn)
        
        self.info_panel = QGroupBox(lang_mgr.tr("info_panel"))
        info_layout = QHBoxLayout()
        self.paths_text = QTextEdit()
        self.paths_text.setReadOnly(True)
        self.paths_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.ports_text = QTextEdit()
        self.ports_text.setReadOnly(True)
        self.ports_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        info_layout.addWidget(self.paths_text, 1)
        info_layout.addWidget(self.ports_text, 1)
        self.info_panel.setLayout(info_layout)
        content_layout.addWidget(self.info_panel)
        
        content.setLayout(content_layout)
        main_layout.addWidget(content)
        central.setLayout(main_layout)
        self.setCentralWidget(central)
        
        self.add_log(lang_mgr.tr("base_dir") + f" {BASE_DIR}", "info")
        self.add_log(lang_mgr.tr("auto_start"), "info")
    
    def adjust_text_height(self, text_edit):
        doc_height = text_edit.document().size().height()
        margin = text_edit.document().documentMargin()
        frame_width = text_edit.frameWidth() * 2
        total_height = doc_height + margin * 2 + frame_width + 10
        text_edit.setFixedHeight(int(total_height))
    
    def get_paths_info(self):
        paths = [
            f"{lang_mgr.tr('tor_exe')} {TOR_EXE}",
            f"{lang_mgr.tr('tor_config')} {TORRC}",
            f"{lang_mgr.tr('bridges_file')} {BRIDGE_FILE}",
            f"{lang_mgr.tr('lyrebird')} {LYREBIRD_EXE}",
            f"{lang_mgr.tr('conjure')} {CONJURE_EXE}",
        ]
        for i, p in enumerate(paths):
            file_path = p.split(': ', 1)[1] if ': ' in p else p.split(' ', 1)[1]
            if not os.path.exists(file_path):
                paths[i] += " " + lang_mgr.tr("not_found")
        return "\n".join(paths)
    
    def check_and_fix_all_paths(self):
        os.makedirs(os.path.dirname(TOR_EXE), exist_ok=True)
        os.makedirs(os.path.dirname(TORRC), exist_ok=True)
        
        missing = []
        if not os.path.exists(TOR_EXE):
            missing.append(TOR_EXE)
        if not os.path.exists(LYREBIRD_EXE):
            missing.append(LYREBIRD_EXE)
        if not os.path.exists(CONJURE_EXE):
            missing.append(CONJURE_EXE)
        
        if missing:
            self.add_log(f"{lang_mgr.tr('missing_files')} {', '.join(missing)}", "warn")
            self.show_toast(lang_mgr.tr("missing_transports"), is_error=True)
        
        self.fix_paths_in_torrc()
    
    def fix_paths_in_torrc(self):
        if not os.path.exists(TORRC):
            self.create_default_torrc()
            return
        
        try:
            with open(TORRC, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            new_lines = []
            geoip_path = os.path.join(BASE_DIR, "data", "geoip")
            geoip6_path = os.path.join(BASE_DIR, "data", "geoip6")
            
            for line in lines:
                if re.match(r'^\s*GeoIPFile\s', line, re.IGNORECASE):
                    new_line = f"GeoIPFile {geoip_path}\n"
                    if new_line != line:
                        modified = True
                    new_lines.append(new_line)
                elif re.match(r'^\s*GeoIPv6File\s', line, re.IGNORECASE):
                    new_line = f"GeoIPv6File {geoip6_path}\n"
                    if new_line != line:
                        modified = True
                    new_lines.append(new_line)
                elif 'lyrebird' in line.lower() and '.exe' in line.lower():
                    exec_idx = line.lower().find('exec')
                    if exec_idx != -1:
                        after_exec = line[exec_idx+4:].lstrip()
                        space_idx = after_exec.find(' ')
                        args = after_exec[space_idx:] if space_idx != -1 else ''
                        new_line = line[:exec_idx] + f"exec {LYREBIRD_EXE}{args}\n"
                        if new_line != line:
                            modified = True
                        new_lines.append(new_line)
                    else:
                        new_lines.append(line)
                elif 'conjure-client.exe' in line.lower():
                    exec_idx = line.lower().find('exec')
                    if exec_idx != -1:
                        after_exec = line[exec_idx+4:].lstrip()
                        space_idx = after_exec.find(' ')
                        args = after_exec[space_idx:] if space_idx != -1 else ''
                        new_line = line[:exec_idx] + f"exec {CONJURE_EXE}{args}\n"
                        if new_line != line:
                            modified = True
                        new_lines.append(new_line)
                    else:
                        new_lines.append(line)
                elif re.match(r'^\s*%include\s', line, re.IGNORECASE):
                    new_line = f"%include {BRIDGE_FILE}\n"
                    if new_line != line:
                        modified = True
                    new_lines.append(new_line)
                else:
                    new_lines.append(line)
            
            filtered_lines = [line for line in new_lines if line.strip() != '']
            if len(filtered_lines) != len(new_lines):
                modified = True
                new_lines = filtered_lines
            
            if modified:
                with open(TORRC, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                self.add_log(lang_mgr.tr("paths_updated"), "info")
                self.show_toast(lang_mgr.tr("config_updated"), is_error=False)
        except Exception as e:
            self.add_log(f"{lang_mgr.tr('error_updating_torrc')} {e}", "error")
            self.show_toast(f"{lang_mgr.tr('error_updating_torrc')} {e}", is_error=True)
    
    def create_default_torrc(self):
        try:
            geoip_path = os.path.join(BASE_DIR, "data", "geoip")
            geoip6_path = os.path.join(BASE_DIR, "data", "geoip6")
            content = f"""# torrc generated by Onion Manager
AvoidDiskWrites 1
Log notice stdout
CookieAuthentication 1
DormantCanceledByStartup 1
GeoIPFile {geoip_path}
GeoIPv6File {geoip6_path}
ClientTransportPlugin meek_lite,obfs2,obfs3,obfs4,scramblesuit,webtunnel exec {LYREBIRD_EXE}
ClientTransportPlugin snowflake exec {LYREBIRD_EXE}
ClientTransportPlugin conjure exec {CONJURE_EXE} -registerURL https://registration.refraction.network/api
ExcludeNodes {{ru}}, {{by}}, {{ua}}, {{kz}}
StrictNodes 1
UseBridges 1
HTTPTunnelPort 9051
SOCKSPort 9050

%include {BRIDGE_FILE}
"""
            os.makedirs(os.path.dirname(TORRC), exist_ok=True)
            with open(TORRC, 'w', encoding='utf-8') as f:
                f.write(content)
            self.add_log(lang_mgr.tr("default_torrc_created"), "info")
        except Exception as e:
            self.add_log(f"{lang_mgr.tr('error_creating_torrc')} {e}", "error")
    
    def get_ports_info(self):
        info = []
        try:
            with open(TORRC, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if re.match(r'^SOCKSPort\s', line, re.IGNORECASE):
                        parts = line.split()
                        if len(parts) >= 2:
                            info.append(f"SOCKS5 proxy: {parts[1]}")
                    elif re.match(r'^HTTPTunnelPort\s', line, re.IGNORECASE):
                        parts = line.split()
                        if len(parts) >= 2:
                            info.append(f"HTTP proxy: {parts[1]}")
                    elif re.match(r'^ControlPort\s', line, re.IGNORECASE):
                        parts = line.split()
                        if len(parts) >= 2:
                            info.append(f"Control port: {parts[1]}")
                    elif re.match(r'^%include\s', line, re.IGNORECASE):
                        parts = line.split(maxsplit=1)
                        if len(parts) >= 2:
                            info.append(f"Bridges include: {parts[1]}")
            if not info:
                info.append(lang_mgr.tr("ports_not_found"))
        except Exception as e:
            info.append(f"Ошибка чтения torrc: {e}")
        return "\n".join(info)
    
    def update_system_info(self):
        self.paths_text.setPlainText(self.get_paths_info())
        self.ports_text.setPlainText(self.get_ports_info())
        self.adjust_text_height(self.paths_text)
        self.adjust_text_height(self.ports_text)
    
    def show_toast(self, message, is_error=False):
        ToastNotification.show_toast(self, message, is_error)
    
    def add_log(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "warn" or "warn" in message.lower():
            self.warn_text.append(f"[{timestamp}] {message}")
        elif level == "error" or "error" in message.lower() or "err" in message.lower():
            self.error_text.append(f"[{timestamp}] {message}")
        if level != "warn" and level != "error" and "warn" not in message.lower() and "error" not in message.lower() and "err" not in message.lower():
            self.log_text.append(f"[{timestamp}] {message}")
        else:
            color = "#dcdcaa" if "warn" in message.lower() else "#f48771"
            self.log_text.append(f"<font color='{color}'>[{timestamp}] {message}</font>")
        self.log_text.ensureCursorVisible()
        self.warn_text.ensureCursorVisible()
        self.error_text.ensureCursorVisible()
    
    def update_status(self, message):
        self.status_label.setText(f"📊 {message}")
        self.add_log(message, "info")
    
    def start_tor(self):
        self.update_system_info()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.restart_btn.setEnabled(True)
        self.is_running = True
        self.update_status(lang_mgr.tr("starting"))
        threading.Thread(target=self._start_thread, daemon=True).start()
    
    def _start_thread(self):
        if self.worker.start_tor():
            self.update_status(lang_mgr.tr("tor_started").replace("✅ Tor запущен (PID: ", "").replace(")", ""))
        else:
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.restart_btn.setEnabled(False)
            self.is_running = False
    
    def stop_tor(self):
        self.worker.stop_tor()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        self.is_running = False
    
    def restart_tor(self):
        self.update_system_info()
        self.clear_logs()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        self.update_status(lang_mgr.tr("restarting"))
        threading.Thread(target=self._restart_thread, daemon=True).start()
    
    def _restart_thread(self):
        if self.worker.restart_tor():
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.restart_btn.setEnabled(True)
            self.update_status(lang_mgr.tr("tor_started"))
        else:
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.restart_btn.setEnabled(False)
            self.is_running = False
    
    def load_bridge_config(self):
        try:
            if os.path.exists(self.bridge_file):
                with open(self.bridge_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                lines = content.split('\n')
                cleaned = []
                for line in lines:
                    stripped = line.strip()
                    if stripped.lower().startswith('bridge'):
                        cleaned.append(stripped[6:].lstrip())
                    else:
                        cleaned.append(line)
                self.bridge_edit.setPlainText('\n'.join(cleaned).rstrip('\n'))
                self.add_log(lang_mgr.tr("bridges_loaded"), "info")
                self.show_toast(lang_mgr.tr("bridges_loaded"), is_error=False)
            else:
                self.add_log(f"{lang_mgr.tr('bridge_file_not_found')} {self.bridge_file}", "warn")
                self.bridge_edit.setPlainText("")
                self.show_toast(lang_mgr.tr("bridge_file_not_found"), is_error=True)
        except Exception as e:
            self.add_log(f"{lang_mgr.tr('error_loading_bridges')} {e}", "error")
            self.show_toast(f"{lang_mgr.tr('error_loading_bridges')} {e}", is_error=True)
    
    def save_bridge_config(self):
        try:
            content = self.bridge_edit.toPlainText()
            lines = content.strip().split('\n')
            formatted = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    formatted.append(f"bridge {line}")
                elif line:
                    formatted.append(line)
            os.makedirs(os.path.dirname(self.bridge_file), exist_ok=True)
            with open(self.bridge_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(formatted))
            self.add_log(lang_mgr.tr("bridges_saved"), "info")
            self.show_toast(lang_mgr.tr("bridges_saved"), is_error=False)
        except Exception as e:
            self.add_log(f"{lang_mgr.tr('error_saving_bridges')} {e}", "error")
            self.show_toast(f"{lang_mgr.tr('error_saving_bridges')} {e}", is_error=True)
    
    def clear_logs(self):
        self.log_text.clear()
        self.warn_text.clear()
        self.error_text.clear()
        self.add_log(lang_mgr.tr("logs_cleared"), "info")
    
    def closeEvent(self, event):
        self.worker.stop_tor()
        self.thread.quit()
        self.thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Onion Manager")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())