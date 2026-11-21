from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class LauncherSettings:
    name: str = "Steve"
    debug: bool = False
    release: bool = True
    snapshot: bool = False
    old_beta: bool = False
    old_alpha: bool = False
    check_files: bool = True
    random_theme: bool = True
    selected_theme: int = 1
    custom_image: str = ""
    custom_theme: str = ""
    hide: bool = False
    mine_path: str = ""
    memory_args: str = "2048"
    custom_args: str = ""
    ely_by: bool = False
    custom_skin: str = ""
    default_skin: bool = True
    language: str = ""
    default_path: bool = True
    java_paths: list[str] = field(default_factory=list)
    java: str = "Latest"

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "LauncherSettings":
        known = cls.__dataclass_fields__
        return cls(**{key: value for key, value in values.items() if key in known})

    def to_dict(self) -> dict[str, Any]:
        return {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
        }


@dataclass(slots=True)
class VersionState:
    download: list[str] = field(default_factory=list)
    not_comp: list[str] = field(default_factory=list)
    version: str = ""
    profile: str | bool = False

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "VersionState":
        known = cls.__dataclass_fields__
        return cls(**{key: value for key, value in values.items() if key in known})

    def to_dict(self) -> dict[str, Any]:
        return {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
        }


@dataclass(slots=True)
class LaunchSession:
    selected_version: str = ""
    username: str = "Steve"
    game_directory: Path | None = None
    process: Any = None
    log_file: Any = None
    running: bool = False
    downloaded_files: int = 0
    total_files: int = 0
    status: str = ""
