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
## 🔗 Где взять Tor / Where to get Tor

**Русский:**

Для работы **Onion Manager** вам понадобятся файлы самого Tor и подключаемых транспортов (pluggable transports). Скачать официальный **Tor Expert Bundle** можно по ссылке:

👉 [https://www.torproject.org/download/tor/](https://www.torproject.org/download/tor/)

На этой странице выберите версию для вашей операционной системы (например, `Windows (x86_64)`). Это не браузер, а набор файлов (`tor.exe`, `lyrebird.exe`, `conjure-client.exe` и другие), которые программа использует для работы.

> **Важно:** Ссылка приведена исключительно для обеспечения технической совместимости программы. Данный проект создан независимо от анонимного программного обеспечения Tor® и не дает никаких гарантий от The Tor Project в отношении качества, пригодности или чего-либо еще.

**English:**

To run **Onion Manager**, you need the core Tor and pluggable transport files. You can download the official **Tor Expert Bundle** here:

👉 [https://www.torproject.org/download/tor/](https://www.torproject.org/download/tor/)

On this page, choose the version for your operating system (e.g., `Windows (x86_64)`). This is not a browser, but a set of files (`tor.exe`, `lyrebird.exe`, `conjure-client.exe`, and others) that the application uses to function.

> **Note:** This link is provided solely for technical compatibility purposes. This project is created independently from the Tor® anonymity software and carries no guarantee from The Tor Project regarding quality, suitability, or anything else.
## 📦 Загрузка готовой версии / Download built release

**Русский:**  
Готовая исполняемая версия (EXE-файл) доступна в разделе [Releases](https://github.com/lavrov-veleslav/OnionManager/releases).  
Последняя стабильная версия: [v1.0.0](https://github.com/lavrov-veleslav/OnionManager/releases/tag/v1.0.0)

**English:**  
The pre-built executable (EXE) is available in the [Releases](https://github.com/lavrov-veleslav/OnionManager/releases) section.  
Latest stable release: [v1.0.0](https://github.com/lavrov-veleslav/OnionManager/releases/tag/v1.0.0)
