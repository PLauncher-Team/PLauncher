import os
from collections.abc import Callable, MutableMapping
from typing import Any


class JavaController:
    def __init__(
        self,
        *,
        settings: MutableMapping[str, Any],
        java_runtime: Any,
        available_major_versions: Callable[[], list[int]],
        launcher_api: Any,
        minecraft_directory: Callable[[], str],
        language_manager: Any,
        java_selector: Any,
        file_dialog: Any,
        process_api: Any,
        save_settings: Callable[[], None],
        logger: Callable[..., None],
        notify_error: Callable[[str, str], None],
        confirm_delete: Callable[[str], bool],
    ) -> None:
        self.settings = settings
        self.java_runtime = java_runtime
        self.available_major_versions = available_major_versions
        self.launcher_api = launcher_api
        self.minecraft_directory = minecraft_directory
        self.language_manager = language_manager
        self.java_selector = java_selector
        self.file_dialog = file_dialog
        self.process_api = process_api
        self.save_settings = save_settings
        self.logger = logger
        self.notify_error = notify_error
        self.confirm_delete = confirm_delete

    def _text(self, key: str) -> str:
        return self.language_manager.get(key)

    def get_java_path(self) -> str | bool:
        runtimes = self.launcher_api.runtime.get_installed_jvm_runtimes(
            self.minecraft_directory()
        )
        if not runtimes:
            return False
        return self.launcher_api.runtime.get_executable_path(
            runtimes[0], self.minecraft_directory()
        )

    def get_java_options(self) -> list[str]:
        return (
            [self._text("settings.2_page.latest_java")]
            + [self._text("settings.2_page.recommended_java")]
            + self.settings["java_paths"]
            + [f"Java {version}" for version in self.available_major_versions()]
            + [self._text("settings.2_page.add")]
        )

    def select_java_path(self) -> str:
        return self.file_dialog.askopenfilename(
            title=self._text("settings.2_page.select_java"),
            filetypes=[(self._text("settings.2_page.java_exe"), "java.exe")],
        )

    def check_java(self, java_path: str) -> bool:
        for option in ("-version", "--version"):
            try:
                result = self.process_api.run(
                    [java_path, option],
                    capture_output=True,
                    text=True,
                    creationflags=self.process_api.CREATE_NO_WINDOW,
                )
                if result.returncode == 0:
                    return True
            except Exception:
                continue
        return False

    def add_java(self) -> None:
        path = self.select_java_path()
        if not path:
            return
        known_paths = self.settings["java_paths"] + self.java_runtime.get_all_javas_exe()
        if os.path.normcase(path) in map(os.path.normcase, known_paths):
            self.logger(f"Java установка уже существует: {path}", "WARNING")
            return
        if self.check_java(path):
            self.logger(f"Добавление Java установки: {path}")
            self.settings["java_paths"].append(path)
            self.save_settings()
            self.java_selector.configure(values=self.get_java_options())
            return
        self.logger(f"Не удалось добавить Java установку: {path}", level="ERROR")
        self.notify_error(
            self._text("messages.titles.error"),
            self._text("messages.texts.error.java"),
        )

    def on_select_java(self, name: str) -> None:
        if name == self._text("settings.2_page.add"):
            selected = self.settings["java"]
            if selected == "Stable":
                self.java_selector.set(self._text("settings.2_page.recommended_java"))
            elif selected == "Latest":
                self.java_selector.set(self._text("settings.2_page.latest_java"))
            else:
                self.java_selector.set(selected)
            self.add_java()
            return
        if name == self._text("settings.2_page.recommended_java"):
            self.settings["java"] = "Stable"
            self.logger("Выбрана рекомендуемая Java версия")
        elif name == self._text("settings.2_page.latest_java"):
            self.settings["java"] = "Latest"
            self.logger("Выбрана последняя Java версия")
        else:
            self.settings["java"] = name
            self.logger(f"Выбрана Java: {name}")
        self.save_settings()

    def delete_java(self) -> None:
        current = self.java_selector.get()
        if current in (
            self._text("settings.2_page.recommended_java"),
            self._text("settings.2_page.latest_java"),
        ):
            return
        if not self.confirm_delete(current):
            return
        self.logger(f"Удаление Java установки: {current}")
        self.settings["java"] = "Latest"
        self.settings["java_paths"].remove(current)
        self.save_settings()
        self.java_selector.set(self._text("settings.2_page.latest_java"))
        self.java_selector.configure(values=self.get_java_options())
