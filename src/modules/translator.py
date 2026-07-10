from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


class Translator:
    def __init__(self, language: str = None):
        supported_languages = {"ru", "en", "be", "es", "uk"}

        if not language:
            sys_locale = getdefaultlocale()[0]
            if sys_locale:
                lang_code = sys_locale.split("_")[0].lower()
                self.language = lang_code if lang_code in supported_languages else "en"
            else:
                self.language = "ru"
            LauncherConfig.config["language"] = self.language
            save_config()
        else:
            self.language = language

        self.translations: dict = {}
        self._load_translations()

    def _load_translations(self):
        try:
            path = os.path.join("locales", f"{self.language}.json")
            with open(path, encoding="utf-8") as f:
                self.translations = json.load(f)
        except FileNotFoundError:
            log(f"Файл перевода не найден: {path}", level="ERROR", source="translator")
            self.translations = {}

    def get(self, key: str, default: str = None) -> str:
        keys = key.split(".")
        result = self.translations
        try:
            for k in keys:
                result = result[k]
            return result
        except (KeyError, TypeError):
            return default or key


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
    texts_language_reverse = {
        "Русский": "ru",
        "Українська": "uk",
        "Беларуский": "be",
        "English": "en",
        "Español": "es"
    }

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
        log("Перезапуск приложения для смены языка", source="translator")
        root.destroy()
        kernel32.ReleaseMutex(mutex)
        restart_app_with_bat()
