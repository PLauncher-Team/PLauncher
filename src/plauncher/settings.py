import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .config import ConfigStore, DEFAULT_SETTINGS, DEFAULT_VERSION, VersionStore


class LauncherSettingsService:
    def __init__(
        self,
        *,
        config_path: Path | str,
        minecraft_directory: Path | str,
        memory_megabytes: int,
        logger: Callable[..., None],
    ) -> None:
        defaults = dict(DEFAULT_SETTINGS)
        defaults["memory_args"] = str(memory_megabytes)
        self.defaults = defaults
        self.logger = logger
        self.config_store = ConfigStore(Path(config_path), defaults)
        self.version_store = VersionStore(Path(minecraft_directory) / "version.json", DEFAULT_VERSION)
        self.config: dict[str, Any] = {}
        self.version: dict[str, Any] = {}

    def load_config(self, themes_directory: Path | str) -> tuple[dict[str, Any], bool]:
        exists = self.config_store.path.is_file()
        self.config = self.config_store.load()
        self._clear_missing_path("custom_image", Path)
        self._clear_missing_path("custom_skin", Path)
        custom_theme = self.config["custom_theme"]
        if custom_theme and not (Path(themes_directory) / f"{custom_theme}.json").is_file():
            self.logger(f"Файл темы не найден: {custom_theme}", "WARNING")
            self.config["custom_theme"] = self.defaults["custom_theme"]
        self.config = dict(sorted(self.config.items()))
        self.save_config()
        return self.config, exists

    def load_version(self, minecraft_directory: Path | str) -> tuple[dict[str, Any], bool]:
        self.version_store.path = Path(minecraft_directory) / "version.json"
        exists = self.version_store.path.is_file()
        self.version = self.version_store.load()
        self.save_version()
        return self.version, exists

    def save_config(self) -> None:
        self.config_store.save(self.config)

    def save_version(self) -> None:
        self.version_store.save(self.version)

    def _clear_missing_path(self, key: str, path_factory: Callable[[str], Path]) -> None:
        value = self.config[key]
        if value and not path_factory(value).is_file():
            self.logger(f"Файл не найден: {value}", "WARNING")
            self.config[key] = self.defaults[key]
