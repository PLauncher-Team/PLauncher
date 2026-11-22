from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..services.profiles import ProfileService


class ProfileController:
    def __init__(
        self,
        *,
        profile_service: ProfileService,
        language_manager: Any,
        profile_selector: Any,
        name_entry: Any,
        add_button: Any,
        delete_button: Any,
        rename_button: Any,
        open_button: Any,
        get_active_profile: Callable[[], str | bool],
        set_active_profile: Callable[[str | bool], None],
        save_active_profile: Callable[[], None],
        confirm_delete: Callable[[str], bool],
        notify_error: Callable[[str, str], None],
        refresh_mod_viewer: Callable[[], None],
        logger: Callable[..., None],
        open_path: Callable[[Path], None],
    ) -> None:
        self.profile_service = profile_service
        self.language_manager = language_manager
        self.profile_selector = profile_selector
        self.name_entry = name_entry
        self.add_button = add_button
        self.delete_button = delete_button
        self.rename_button = rename_button
        self.open_button = open_button
        self.get_active_profile = get_active_profile
        self.set_active_profile = set_active_profile
        self.save_active_profile = save_active_profile
        self.confirm_delete = confirm_delete
        self.notify_error = notify_error
        self.refresh_mod_viewer = refresh_mod_viewer
        self.logger = logger
        self.open_path = open_path

    def _text(self, key: str) -> str:
        return self.language_manager.get(key)

    def list_profiles(self) -> list[str]:
        return [self._text("settings.4_page.no")] + self.profile_service.list_profiles()

    def select_profile(self, *_args: Any) -> None:
        current = self.profile_selector.get()
        no_profile = self._text("settings.4_page.no")
        self.set_active_profile(False if current == no_profile else current)
        self.save_active_profile()
        self.refresh_mod_viewer()
        self.logger(f"Выбран профиль: {current}")

    def delete_current(self) -> None:
        current = self.profile_selector.get()
        no_profile = self._text("settings.4_page.no")
        if current == no_profile or not self.confirm_delete(current):
            return

        self.logger(f"Удаление профиля: {current}")
        self.profile_service.delete(current)
        self.profile_selector.configure(values=self.list_profiles())
        values = self.profile_selector.cget("values")
        first = values[0] if values and values[0] != "" else no_profile
        self.profile_selector.set(first)
        self.set_active_profile(False if first == no_profile else first)
        self.save_active_profile()
        self.logger(f"Профиль {current} успешно удалён")

    def _restore_edit_controls(self) -> None:
        self.name_entry.delete(0, "end")
        self.name_entry.lower()
        self.delete_button.configure(
            text=self._text("settings.4_page.delete"), command=self.delete_current
        )
        self.add_button.configure(
            text=self._text("settings.4_page.add"), command=self.begin_add
        )
        self.profile_selector.configure(state="readonly")
        self.open_button.configure(state="normal")
        self.rename_button.configure(state="normal")

    def begin_add(self) -> None:
        self.name_entry.delete(0, "end")
        self.name_entry.lift()
        self.rename_button.configure(state="disabled")
        self.profile_selector.configure(state="disabled")
        self.open_button.configure(state="disabled")
        self.delete_button.configure(
            text=self._text("messages.answers.no"), command=self._restore_edit_controls
        )
        self.add_button.configure(
            text=self._text("settings.4_page.save"), command=self.save_new_profile
        )

    def save_new_profile(self) -> None:
        name = self.name_entry.get().strip()
        no_profile = self._text("settings.4_page.no")
        if not name or name == no_profile:
            return

        self.logger(f"Создание нового профиля: {name}")
        try:
            self.profile_service.create(name)
        except Exception as error:
            self.logger(f"Не удалось создать профиль {name}: {error}", level="ERROR")
            self.notify_error(
                self._text("messages.titles.error"),
                self._text("messages.texts.error.profile_add") + str(error),
            )
            return

        self.logger(
            f"Профиль {name} успешно создан с {len(self.profile_service.DIRECTORIES)} директориями"
        )
        if self.profile_selector.cget("values") == (no_profile,):
            self.set_active_profile(name)
            self.profile_selector.set(name)
            self.save_active_profile()
        self.save_active_profile()
        self.profile_selector.configure(values=self.list_profiles())
        self._restore_edit_controls()

    def begin_rename(self) -> None:
        current = self.profile_selector.get()
        if current == self._text("settings.4_page.no"):
            return

        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, current)
        self.name_entry.lift()
        self.rename_button.configure(state="disabled")
        self.profile_selector.configure(state="disabled")
        self.open_button.configure(state="disabled")
        self.delete_button.configure(
            text=self._text("messages.answers.no"), command=self._restore_edit_controls
        )
        self.add_button.configure(
            text=self._text("settings.4_page.save"),
            command=lambda: self.rename_profile(current),
        )

    def rename_profile(self, old_name: str) -> None:
        new_name = self.name_entry.get().strip()
        no_profile = self._text("settings.4_page.no")
        if not new_name or new_name == old_name or new_name == no_profile:
            return

        try:
            self.profile_service.rename(old_name, new_name)
        except Exception as error:
            self.logger("Не удалось переименовать профиль:", level="ERROR")
            self.notify_error(
                self._text("messages.titles.error"),
                self._text("messages.texts.error.profile_rename") + str(error),
            )
            return

        self.logger("Профиль успешно переименован")
        if self.get_active_profile() == old_name:
            self.profile_selector.set(new_name)
            self.set_active_profile(new_name)
            self.save_active_profile()
        self.profile_selector.configure(values=self.list_profiles())
        self._restore_edit_controls()
        self.profile_selector.set(new_name)

    def open_folder(self) -> None:
        current = self.profile_selector.get()
        if current == self._text("settings.4_page.no"):
            return
        path = self.profile_service.profile_path(current)
        self.logger(f"Открытие папки профиля: {path}")
        self.open_path(path)
