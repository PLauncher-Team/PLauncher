import threading
from collections.abc import Callable
from typing import Any


class LoaderController:
    LOADERS = ("Forge", "Fabric", "NeoForge", "OptiFine", "Quilt", "Cleanroom")

    def __init__(
        self,
        *,
        online: bool,
        catalog: Any,
        installer: Any,
        version_selector: Any,
        version_dropdown: Any,
        loader_selector: Any,
        progress_bar: Any,
        install_button: Any,
        launch_button: Any,
        settings_frame: Any,
        language_manager: Any,
        logger: Callable[..., None],
        notify_error: Callable[[str, str], None],
        set_maximum: Callable[[int], None],
        update_progress: Callable[[int, Any, bool], None],
        reload_versions: Callable[[], None],
        current_process: Callable[[], Any],
        kill_thread: Callable[[threading.Thread], Any],
    ) -> None:
        self.online = online
        self.catalog = catalog
        self.installer = installer
        self.version_selector = version_selector
        self.version_dropdown = version_dropdown
        self.loader_selector = loader_selector
        self.progress_bar = progress_bar
        self.install_button = install_button
        self.launch_button = launch_button
        self.settings_frame = settings_frame
        self.language_manager = language_manager
        self.logger = logger
        self.notify_error = notify_error
        self.set_maximum = set_maximum
        self.update_progress = update_progress
        self.reload_versions = reload_versions
        self.current_process = current_process
        self.kill_thread = kill_thread
        self.versions: dict[str, list[str]] = {name: [] for name in self.LOADERS}
        self.neoforge_versions: dict[str, Any] = {}

    def _text(self, key: str) -> str:
        return self.language_manager.get(key)

    def list_versions(self, loader: str) -> list[str]:
        versions = self.versions.get(loader, []) if self.online else []
        self.version_dropdown.configure(values=versions)
        if versions:
            self.version_selector.set(versions[0])
        return list(versions)

    def install_selected(self) -> None:
        selected_version = self.version_selector.get()
        selected_loader = self.loader_selector.get()
        if not selected_version or not selected_loader:
            return
        callbacks = {
            "setMax": self.set_maximum,
            "setProgress": lambda value: self.update_progress(
                value, self.progress_bar, False
            ),
        }
        try:
            self.installer.install(
                selected_loader,
                selected_version,
                callback=callbacks,
                neoforge_versions=self.neoforge_versions,
            )
            self.settings_frame.after_idle(self.reload_versions)
            self.logger("Установка успешно завершена")
        except Exception as error:
            self.logger(f"Ошибка установки загрузчика: {error}", level="ERROR")
            self.notify_error(
                self._text("messages.titles.error"),
                self._text("messages.texts.error.loading_loader")
                + str(error.__class__.__name__),
            )

    def install_with_controls(self) -> None:
        download_thread = threading.Thread(target=self.install_selected)
        download_thread.start()

        def cancel() -> None:
            self.install_button.configure(
                state="disabled", text=self._text("main.status.finalizing")
            )
            self.kill_thread(download_thread)
            process = self.current_process()
            if process is not None:
                process.terminate()

        self.install_button.configure(
            command=cancel,
            text=self._text("settings.4_page.cancel_loading"),
        )
        self.launch_button.configure(state="disabled")
        download_thread.join()
        self.progress_bar.set(0)
        self.install_button.configure(
            state="normal",
            text=self._text("settings.4_page.install_loader"),
            command=lambda: threading.Thread(
                target=self.install_with_controls
            ).start(),
        )
        self.launch_button.configure(state="normal")

    def load_catalogs(self) -> None:
        if not self.online:
            return
        for name in self.LOADERS:
            threading.Thread(target=self._load_catalog, args=(name,), daemon=True).start()

    def _load_catalog(self, name: str) -> None:
        try:
            versions, metadata = self.catalog.fetch(name)
            self.versions[name].extend(versions)
            if name == "NeoForge":
                self.neoforge_versions = metadata
            self.logger(f"Загружено версий для {name}: {len(versions)}.", "INFO")

            def update_ui() -> None:
                available_loaders = list(self.loader_selector.cget("values"))
                if name not in available_loaders:
                    available_loaders.append(name)
                    self.loader_selector.configure(values=available_loaders)
                    if not self.loader_selector.get():
                        self.loader_selector.set(name)
                if self.loader_selector.get() == name:
                    self.version_dropdown.configure(values=versions)
                    if versions:
                        self.version_selector.set(versions[0])

            self.settings_frame.after_idle(update_ui)
        except Exception as error:
            self.logger(f"Ошибка получения версий для {name}: {error}", "WARNING")
