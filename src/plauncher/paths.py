from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppPaths:
    root: Path
    source: Path
    modules: Path
    locales: Path
    themes: Path
    images: Path
    logs: Path
    config_file: Path
    minecraft_default: Path

    @classmethod
    def from_root(cls, root: Path | str) -> "AppPaths":
        root_path = Path(root).expanduser().resolve()
        source_path = root_path / "src"
        app_data = Path.home() / "AppData" / "Roaming"
        if app_data.exists():
            minecraft_default = app_data / ".minecraft"
        else:
            minecraft_default = Path.home() / ".minecraft"
        return cls(
            root=root_path,
            source=source_path,
            modules=source_path / "modules",
            locales=source_path / "locales",
            themes=source_path / "themes",
            images=source_path / "png",
            logs=root_path / "launcher.log",
            config_file=root_path / "data.json",
            minecraft_default=minecraft_default,
        )

    def ensure_directories(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.minecraft_default.mkdir(parents=True, exist_ok=True)
