import json
from pathlib import Path


class MinecraftEnvironmentService:
    DIRECTORIES = (
        "assets",
        "bin",
        "libraries",
        "logs",
        "resourcepacks",
        "saves",
        "screenshots",
        "shaderpacks",
        "versions",
        "profiles",
        "mods",
    )

    def __init__(self, minecraft_directory: Path | str) -> None:
        self.directory = Path(minecraft_directory).expanduser()

    def ensure(self) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        for name in self.DIRECTORIES:
            (self.directory / name).mkdir(parents=True, exist_ok=True)
        self._ensure_launcher_profiles()
        return self.directory

    def _ensure_launcher_profiles(self) -> None:
        profile_file = self.directory / "launcher_profiles.json"
        data = {
            "profiles": {
                "forge": {
                    "name": "forge",
                    "lastVersionId": "1.12.2-forge1.12.2-14.23.0.2501",
                }
            },
            "clientToken": "dd76b195-eb71-4786-b561-7ebd985574bf",
        }
        temporary_file = profile_file.with_suffix(".json.tmp")
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        temporary_file.replace(profile_file)
