# OnionManager
Unofficial GUI manager for Tor Expert Bundle on Windows. A third-party tool to start, stop, monitor, and manage bridges.

# 🧅 Onion Manager

**Русский:** GUI-менеджер для управления Tor Expert Bundle на Windows  
**English:** GUI manager for Tor Expert Bundle on Windows

---

## 📋 Возможности / Features

**Русский:**
- 🚀 Запуск, остановка и перезапуск Tor одной кнопкой
- 🌉 Управление мостами через удобный редактор
- 📊 Мониторинг логов с разделением на информационные, предупреждения и ошибки
- 🔧 Автоматическая генерация и исправление конфигурационного файла `torrc`
- 🧩 Поддержка плагинов lyrebird и conjure

**English:**
- 🚀 Start, stop, and restart Tor with one button
- 🌉 Manage bridges via a convenient editor
- 📊 Log monitoring with separate sections for info, warnings, and errors
- 🔧 Automatic generation and fixing of `torrc` configuration file
- 🧩 Support for lyrebird and conjure pluggable transports

---

## 🛠️ Установка и использование / Installation & Usage

### Требования / Requirements

**Русский:** Windows 7 и выше, установленный Tor Expert Bundle  
**English:** Windows 7 or later, installed Tor Expert Bundle

**Важно / Important:**  
Файл `Onion.pyw` (или `Onion.exe`) **обязан** находиться в той же папке, что и папка `tor` (рядом с ней, не внутри неё).  
**English:** The `Onion.pyw` (or `Onion.exe`) file **must** be placed in the same folder as the `tor` folder (next to it, not inside it).

### Сборка из исходного кода / Building from source

**Русский:**

Если вы хотите самостоятельно собрать исполняемый файл (EXE) из исходного кода:

1. Убедитесь, что у вас установлен Python и все зависимости (`pip install -r requirements.txt`).
2. В корневой папке проекта запустите файл `build.bat` двойным щелчком.
3. Готовый EXE-файл появится в папке `dist`.

**English:**

If you want to build the executable (EXE) from source code yourself:

1. Make sure you have Python and all dependencies installed (`pip install -r requirements.txt`).
2. In the root folder of the project, double-click the `build.bat` file to run it.
3. The finished EXE file will appear in the `dist` folder.
