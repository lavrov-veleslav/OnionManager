from PyQt5.QtCore import QObject, pyqtSignal, QProcess


class TorProcess(QObject):
    # structured signals
    log_line = pyqtSignal(str, str)  # level, text
    started = pyqtSignal(int)
    stopped = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, tor_path: str, torrc: str):
        super().__init__()
        self.tor_path = tor_path
        self.torrc = torrc
        self.proc = QProcess(self)
        self.proc.readyReadStandardOutput.connect(self._on_stdout)
        self.proc.started.connect(self._on_started)
        self.proc.finished.connect(self._on_finished)
        self.proc.errorOccurred.connect(self._on_error)

    def start(self) -> bool:
        if not self.tor_path:
            self.error.emit("Tor path not configured")
            return False
        try:
            args = ["-f", self.torrc]
            self.proc.start(self.tor_path, args)
            return True
        except Exception as e:
            self.error.emit(str(e))
            return False

    def _on_started(self):
        pid = int(self.proc.processId()) if hasattr(self.proc, 'processId') else 0
        self.started.emit(pid)

    def _on_stdout(self):
        data = bytes(self.proc.readAllStandardOutput()).decode('utf-8', errors='ignore')
        for line in data.splitlines():
            lvl = 'info'
            l = line.lower()
            if '[warn]' in l:
                lvl = 'warn'
            if '[err]' in l or '[error]' in l:
                lvl = 'error'
            self.log_line.emit(lvl, line)

    def stop(self):
        if self.proc.state() != QProcess.NotRunning:
            self.proc.terminate()
            # allow it to finish asynchronously

    def restart(self):
        self.stop()
        self.start()

    def _on_finished(self, exit_code, exit_status):
        self.stopped.emit(exit_code)

    def _on_error(self, error):
        self.error.emit(str(error))
