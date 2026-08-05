import os
from onion_manager.utils.file_helpers import backup_file, safe_write
import re


def load_bridges(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        # strip leading 'bridge ' if present
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
        backup_file(path)
        safe_write(path, '\n'.join(formatted))
        return True
    except Exception:
        return False


def _find_ip_port_in_line(line: str) -> str | None:
    # find IPv4:PORT pattern
    m = re.search(r"(?:(?:\d{1,3}\.){3}\d{1,3}):(\d{1,5})", line)
    if not m:
        return None
    ip_port = m.group(0)
    ip, port = ip_port.split(':')
    # Validate IP octets and port
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


def get_active_bridge(path: str) -> str | None:
    """Return the first IP:PORT found in the bridges file, or None if not found.

    This handles common bridge lines like:
      bridge 1.2.3.4:443 cert=... (obfs4)
      bridge 1.2.3.4:9001
    It does not attempt to resolve pluggable transports that don't embed an IP:PORT (e.g., snowflake broker).
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                # If line starts with 'bridge ' remove it
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
