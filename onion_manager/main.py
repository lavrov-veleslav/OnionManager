"""Onion Manager - modular entry point"""
from PyQt5.QtWidgets import QApplication
import sys
from onion_manager.ui.main_window import MainWindow
from onion_manager.utils.logging_setup import setup_logging


def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("Onion Manager")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
