import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS: dict[str, Any] = {
    "name": "Steve",
    "debug": False,
    "release": True,
    "snapshot": False,
    "old_beta": False,
    "old_alpha": False,
    "check_files": True,
    "random_theme": True,
    "selected_theme": 1,
    "custom_image": "",
    "custom_theme": "",
    "hide": False,
    "mine_path": "",
    "memory_args": "2048",
    "custom_args": "",
    "ely_by": False,
    "custom_skin": "",
    "default_skin": True,
    "language": "",
    "default_path": True,
    "java_paths": [],
    "java": "Latest",
}

DEFAULT_VERSION: dict[str, Any] = {
    "download": [],
    "not_comp": [],
    "version": "",
    "profile": False,
}


class JsonStore:
    def __init__(self, path: Path, defaults: dict[str, Any]) -> None:
        self.path = Path(path)
        self.defaults = deepcopy(defaults)

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            data = deepcopy(self.defaults)
            self.save(data)
            return data
        with self.path.open("r", encoding="utf-8") as file:
            stored = json.load(file)
        if not isinstance(stored, dict):
            raise ValueError(f"Expected a JSON object in {self.path}")
        merged = deepcopy(self.defaults)
        merged.update(stored)
        if merged != stored:
            self.save(merged)
        return merged

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_path = tempfile.mkstemp(
            prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.path)
        except Exception:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass
            raise


class ConfigStore(JsonStore):
    def __init__(self, path: Path) -> None:
        super().__init__(path, DEFAULT_SETTINGS)


class VersionStore(JsonStore):
    def __init__(self, path: Path) -> None:
        super().__init__(path, DEFAULT_VERSION)
