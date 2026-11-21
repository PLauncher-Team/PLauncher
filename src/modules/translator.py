import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


def restart_app_with_bat():
    script_path = os.path.abspath(sys.argv[0])
    _, ext = os.path.splitext(script_path.lower())

    if ext == ".exe":
        launcher = f'start "" "{script_path}"'
    else:
        launcher = f'start "" "pythonw" "{script_path}"'

    bat = f"""@echo off
timeout /t 1 > nul
{launcher}
del "%~f0"
"""
    bat_path = os.path.join(os.getcwd(), "restart.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat)

    subprocess.Popen(bat_path, creationflags=subprocess.CREATE_NO_WINDOW)

    kernel32.ReleaseMutex(mutex)
    os._exit(0)


def select_language(selected_value: str):
    texts_language_reverse = {value: key for key, value in language_manager.get_languages_names().items()}
    if LauncherConfig.config["language"] == selected_value:
        return

    new_lang = texts_language_reverse[selected_value]
    LauncherConfig.config["language"] = new_lang
    save_config()

    new_message(
        title=language_manager.get("messages.titles.warning"),
        message=language_manager.get("messages.texts.warning.language"),
        icon="question",
        option_1=language_manager.get("messages.answers.no"),
        option_2=language_manager.get("messages.answers.yes")
    )

    if GuiOptions.msg.get() == language_manager.get("messages.answers.yes"):
        log("Перезапуск приложения для смены языка")
        root.destroy()
        kernel32.ReleaseMutex(mutex)
        restart_app_with_bat()
