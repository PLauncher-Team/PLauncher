class Translator:
    def __init__(self, language: str = None):
        """
        Initialize the Translator with a specified language or detect system locale.
        """
        supported_languages = {"ru", "en"}

        if not language:
            sys_locale = getdefaultlocale()[0]
            if sys_locale:
                lang_code = sys_locale.split("_")[0].lower()
                self.language = lang_code if lang_code in supported_languages else "en"
            else:
                self.language = "ru"
            config["language"] = self.language
            save_config(config)
        else:
            self.language = language

        self.translations: dict = {}
        self._load_translations()

    def _load_translations(self):
        """
        Load translation JSON file based on selected language.
        """
        try:
            path = os.path.join("locales", f"{self.language}.json")
            with open(path, encoding="utf-8") as f:
                self.translations = json.load(f)
        except FileNotFoundError:
            self.translations = {}

    def get(self, key: str, default: str = None) -> str:
        """
        Retrieve a translated value by a dot-separated key.
        If not found, return the default value or the key itself.
        """
        keys = key.split(".")
        result = self.translations
        try:
            for k in keys:
                result = result[k]
            return result
        except (KeyError, TypeError):
            return default or key


def restart_app_with_bat():
    """
    Create and execute a temporary batch file to restart the application.
    The script will delete itself after execution.
    """
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
    """
    Change the application language and prompt for restart if a new language is selected.
    """
    if config["language"] == selected_value:
        return

    config["language"] = texts_language_reverse[selected_value]
    save_config(config)

    new_message(
        title=language_manager.get("messages.titles.warning"),
        message=language_manager.get("messages.texts.warning.language"),
        icon="question",
        option_1=language_manager.get("messages.answers.no"),
        option_2=language_manager.get("messages.answers.yes")
    )

    if msg.get() == language_manager.get("messages.answers.yes"):
        root.destroy()
        kernel32.ReleaseMutex(mutex)
        restart_app_with_bat()