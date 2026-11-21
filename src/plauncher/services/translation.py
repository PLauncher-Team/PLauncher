import json
import locale
from pathlib import Path
from typing import Any, Callable, MutableMapping


class TranslationService:
    def __init__(
        self,
        locales_directory: Path | str,
        language: str | None = None,
        settings: MutableMapping[str, Any] | None = None,
        save_settings: Callable[[], None] | None = None,
        logger: Any = None,
        locale_provider: Callable[[], tuple[str | None, str | None]] | None = None,
    ) -> None:
        self.locales_directory = Path(locales_directory)
        self.settings = settings
        self.save_settings = save_settings
        self.logger = logger
        self.supported_languages = self.get_supported_languages()
        self.language = language

        if not self.language:
            provider = locale_provider or locale.getdefaultlocale
            system_locale = provider()[0]
            self.language = system_locale.split("_")[0].lower() if system_locale else None
            if self.settings is not None:
                self.settings["language"] = self.language
            if self.save_settings is not None:
                self.save_settings()

        if self.language not in self.supported_languages and self.supported_languages:
            self._log(
                "warning",
                f"Localization for {self.language} was not found; using {self.supported_languages[0]}",
            )
            self.language = self.supported_languages[0]

        self.translations = self._load_translations(self.language) if self.language else {}

    def get_supported_languages(self) -> list[str]:
        if not self.locales_directory.is_dir():
            return []
        return [
            path.stem
            for path in self.locales_directory.iterdir()
            if path.is_file() and path.suffix == ".json"
        ]

    def get_languages_names(self) -> dict[str, str]:
        return {
            language: self._load_translations(language).get("language", language)
            for language in self.supported_languages
        }

    def _load_translations(self, language: str | None) -> dict[str, Any]:
        if not language:
            return {}
        path = self.locales_directory / f"{language}.json"
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError(f"Expected a JSON object in {path}")
            return data
        except Exception as error:
            self._log("error", f"Unable to load localization file {path}: {error}")
            return {}

    def get(self, key: str, default: str | None = None) -> Any:
        value: Any = self.translations
        try:
            for part in key.split("."):
                value = value[part]
            return value
        except (KeyError, TypeError):
            self._log("warning", f"Localization key not found: {key}")
            return default or key

    def _log(self, level: str, message: str) -> None:
        if self.logger is None:
            return
        if callable(self.logger):
            self.logger(message, level=level.upper())
            return
        method = getattr(self.logger, level, None)
        if method is not None:
            method(message)
