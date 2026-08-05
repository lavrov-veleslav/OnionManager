import os
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths
TOR_EXE = os.path.join(BASE_DIR, '..', 'tor', 'tor.exe')
TORRC = os.path.join(BASE_DIR, '..', 'data', 'torrc')
BRIDGE_FILE = os.path.join(BASE_DIR, '..', 'data', 'bridge')
LYREBIRD_EXE = os.path.join(BASE_DIR, '..', 'tor', 'pluggable_transports', 'lyrebird.exe')
CONJURE_EXE = os.path.join(BASE_DIR, '..', 'tor', 'pluggable_transports', 'conjure-client.exe')
ICON_PATH = os.path.join(BASE_DIR, '..', 'icon.ico')
LANG_FILE = os.path.join(BASE_DIR, '..', 'lang.json')

# Other defaults
AUTO_START = False  # Do not auto-start Tor by default in modular app
