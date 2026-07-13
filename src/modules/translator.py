import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


class Translator:
    def __init__(self, language: str = None):
        self.supported_languages = self.get_supported_languages()
        
        self.language = None
        if not language:
            sys_locale = getdefaultlocale()[0]
            if sys_locale:
                lang_code = sys_locale.split("_")[0].lower()
                self.language = lang_code
            LauncherConfig.config["language"] = self.language
            save_config()
        else:
            self.language = language
        
        if self.language not in self.supported_languages and self.supported_languages:
            log(f"Файла локализации для языка {self.language} не найдено. Переключаемся на {self.supported_languages[0]}", level="WARNING", source="translator")
            self.language = self.supported_languages[0]
        elif not self.supported_languages:
            log("Не найдено ни одного файла локализации", level="ERROR", source="translator")
            self.translations = {}
            return
        
        self.translations = self._load_translations(self.language)
    
    def get_languages_names(self):
        languages = {}
        for lang in self.supported_languages:
            languages[lang] = self._load_translations(lang)["language"]
        return languages
        
    @staticmethod
    def get_supported_languages():
        return [locale.removesuffix(".json") for locale in os.listdir("locales") if locale.endswith(".json") and os.path.isfile(os.path.join("locales", locale))]
        
    def _load_translations(self, language):
        try:
            path = os.path.join("locales", f"{language}.json")
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"Не удалось загрузить файл локализации: {e}", level="ERROR", source="translator")
            excepthook(*sys.exc_info())
            return {}

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
        log("Перезапуск приложения для смены языка", source="translator")
        root.destroy()
        kernel32.ReleaseMutex(mutex)
        restart_app_with_bat()
