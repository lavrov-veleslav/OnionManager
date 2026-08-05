import os
import shutil


def backup_file(path: str) -> None:
    try:
        if os.path.exists(path):
            bak = path + '.bak'
            shutil.copy2(path, bak)
    except Exception:
        pass


def safe_write(path: str, data: str) -> None:
    temp = path + '.tmp'
    with open(temp, 'w', encoding='utf-8') as f:
        f.write(data)
    os.replace(temp, path)
