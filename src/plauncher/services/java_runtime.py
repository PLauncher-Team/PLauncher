import os
import shutil
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Callable


class JavaRuntimeService:
    DEFAULT_VERSIONS = [8, 11, 17, 21, 25]

    def __init__(
        self,
        minecraft_directory: Path | str,
        user_agent: str,
        online: bool,
        http_client: Any,
        logger: Callable[..., None] | None = None,
        status_message: str = "",
        versions_loaded: Callable[[list[int]], None] | None = None,
        archive_path: Path | str = "java_temp.zip",
    ) -> None:
        self.minecraft_directory = Path(minecraft_directory)
        self.user_agent = user_agent
        self.online = online
        self.http = http_client
        self.logger = logger
        self.status_message = status_message
        self.versions_loaded = versions_loaded
        self.archive_path = Path(archive_path)

    def get_available_major_versions(self) -> list[int]:
        if not self.online:
            versions = list(self.DEFAULT_VERSIONS)
        else:
            try:
                response = self.http.get(
                    "https://api.adoptium.net/v3/info/available_releases",
                    headers={"User-Agent": self.user_agent},
                    timeout=5,
                )
                response.raise_for_status()
                versions = sorted(set(response.json()["available_lts_releases"]))
                self._log(f"Available Java versions: {versions}")
            except Exception as error:
                versions = list(self.DEFAULT_VERSIONS)
                self._log(f"Unable to retrieve Java versions; using defaults: {error}", "WARNING")

        if self.versions_loaded is not None:
            self.versions_loaded(versions)
        return versions

    def get_latest_java(self, version: int | str) -> tuple[str | None, str | None]:
        api_url = (
            f"https://api.adoptium.net/v3/assets/latest/{version}/hotspot"
            "?architecture=x64&image_type=jre&os=windows&vendor=eclipse"
        )
        try:
            response = self.http.get(
                api_url,
                headers={"User-Agent": self.user_agent},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                self._log(f"No Java {version} release data found", "WARNING")
                return None, None
            release = data[0]
            semantic_version = release["version"]["semver"]
            download_url = release["binary"]["package"]["link"]
            self._log(f"Found Java {version} release {semantic_version}")
            return semantic_version, download_url
        except Exception as error:
            self._log(f"Unable to retrieve Java {version}: {error}", "ERROR")
            return None, None

    def get_local_semantic_version(self, target_directory: Path | str) -> str | None:
        release_file = Path(target_directory) / "release"
        if not release_file.is_file():
            return None
        try:
            for line in release_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("SEMANTIC_VERSION="):
                    return line.split("=", 1)[1].strip().strip('"')
        except OSError:
            return None
        return None

    def save_local_semantic_version(self, target_directory: Path | str, version: str) -> None:
        target = Path(target_directory)
        target.mkdir(parents=True, exist_ok=True)
        (target / "release").write_text(
            f'SEMANTIC_VERSION="{version}"\n',
            encoding="utf-8",
        )

    def download_and_extract_java(
        self,
        version: int | str,
        callback: dict[str, Callable[..., None]] | None = None,
    ) -> str | None:
        runtime_directory = self.minecraft_directory / "runtime"
        target_directory = runtime_directory / f"Java {version}"
        self._log(f"Starting Java {version} installation")
        semantic_version, download_url = self.get_latest_java(version)
        if not semantic_version or not download_url:
            return str(target_directory) if target_directory.exists() else None

        java_executable = target_directory / "bin" / "java.exe"
        local_version = self.get_local_semantic_version(target_directory)
        if local_version == semantic_version and java_executable.is_file():
            self._log(f"Java {version} is already installed")
            return str(target_directory.resolve())

        runtime_directory.mkdir(parents=True, exist_ok=True)
        if callback and callback.get("setStatus"):
            callback["setStatus"](self.status_message)

        try:
            response = self.http.get(
                download_url,
                stream=True,
                timeout=300,
                headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            if callback and callback.get("setMax"):
                callback["setMax"](total_size)

            downloaded = 0
            with self.archive_path.open("wb") as archive:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        archive.write(chunk)
                        downloaded += len(chunk)
                        if callback and callback.get("setProgress"):
                            callback["setProgress"](downloaded)

            self._log(f"Java {version} archive downloaded; extracting")
            if target_directory.exists():
                shutil.rmtree(target_directory)

            with zipfile.ZipFile(self.archive_path, "r") as archive:
                for member in archive.infolist():
                    member_path = PurePosixPath(member.filename)
                    if member_path.is_absolute() or ".." in member_path.parts or len(member_path.parts) <= 1:
                        continue
                    relative_parts = member_path.parts[1:]
                    if not relative_parts:
                        continue
                    destination = target_directory.joinpath(*relative_parts)
                    if member.is_dir():
                        destination.mkdir(parents=True, exist_ok=True)
                    else:
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        with archive.open(member) as source, destination.open("wb") as output:
                            shutil.copyfileobj(source, output)

            self.save_local_semantic_version(target_directory, semantic_version)
            self._log(f"Java {version} installed at {target_directory}")
            return str(target_directory.resolve())
        except Exception as error:
            self._log(f"Java {version} installation failed: {error}", "ERROR")
            return None
        finally:
            if self.archive_path.exists():
                self.archive_path.unlink()

    def get_all_javas_exe(self) -> list[str]:
        runtime_directory = self.minecraft_directory / "runtime"
        if not runtime_directory.is_dir():
            return []
        return [
            str(executable.resolve())
            for executable in runtime_directory.glob("*/bin/java.exe")
            if executable.is_file()
        ]

    def get_any_java_exe(self, version: int | str) -> str | None:
        executable = self.minecraft_directory / "runtime" / f"Java {version}" / "bin" / "java.exe"
        return str(executable.resolve()) if executable.is_file() else None

    def _log(self, message: str, level: str = "INFO") -> None:
        if self.logger is not None:
            self.logger(message, level=level)
