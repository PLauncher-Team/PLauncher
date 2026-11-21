import shutil
from pathlib import Path


class ProfileService:
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
        self.minecraft_directory = Path(minecraft_directory).expanduser()
        self.profiles_directory = self.minecraft_directory / "profiles"

    def list_profiles(self) -> list[str]:
        self.profiles_directory.mkdir(parents=True, exist_ok=True)
        return sorted(
            path.name.removeprefix("profile_")
            for path in self.profiles_directory.iterdir()
            if path.is_dir() and path.name.startswith("profile_")
        )

    def profile_path(self, name: str) -> Path:
        normalized_name = self._validate_name(name)
        return self.profiles_directory / f"profile_{normalized_name}"

    def create(self, name: str) -> Path:
        destination = self.profile_path(name)
        destination.mkdir(parents=True, exist_ok=False)
        for directory in self.DIRECTORIES:
            (destination / directory).mkdir(parents=True, exist_ok=True)
        return destination

    def rename(self, old_name: str, new_name: str) -> Path:
        source = self.profile_path(old_name)
        destination = self.profile_path(new_name)
        if not source.is_dir():
            raise FileNotFoundError(source)
        if destination.exists():
            raise FileExistsError(destination)
        source.rename(destination)
        return destination

    def delete(self, name: str) -> None:
        target = self.profile_path(name)
        if not target.is_dir():
            raise FileNotFoundError(target)
        shutil.rmtree(target)

    @staticmethod
    def _validate_name(name: str) -> str:
        normalized_name = name.strip()
        if not normalized_name or normalized_name in {".", ".."}:
            raise ValueError("Profile name cannot be empty")
        if any(character in normalized_name for character in '<>:"/\\|?*'):
            raise ValueError("Profile name contains invalid characters")
        if normalized_name.endswith((".", " ")):
            raise ValueError("Profile name cannot end with a dot or space")
        return normalized_name
