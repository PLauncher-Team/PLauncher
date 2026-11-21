from dataclasses import dataclass
import os
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
    def from_root(
        cls,
        root: Path | str,
        minecraft_directory: Path | str | None = None,
    ) -> "AppPaths":
        root_path = Path(root).expanduser().resolve()
        source_path = root_path / "src"
        app_data = os.getenv("APPDATA")
        minecraft_default = (
            Path(minecraft_directory).expanduser()
            if minecraft_directory is not None
            else Path(app_data) / ".minecraft" if app_data else Path.home() / ".minecraft"
        )
        return cls(
            root=root_path,
            source=source_path,
            modules=source_path / "modules",
            locales=source_path / "locales",
            themes=source_path / "themes",
            images=source_path / "png",
            logs=source_path / "launcher.log",
            config_file=source_path / "data.json",
            minecraft_default=minecraft_default,
        )

    def ensure_directories(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.source.mkdir(parents=True, exist_ok=True)
        self.minecraft_default.mkdir(parents=True, exist_ok=True)
