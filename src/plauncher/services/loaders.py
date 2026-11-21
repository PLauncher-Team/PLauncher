import os
import subprocess
from pathlib import Path
from typing import Any, Callable


class LoaderInstallationService:
    def __init__(
        self,
        minecraft_directory: Path | str,
        java_runtime: Any,
        available_java_versions: Callable[[], list[int]],
        launcher_api: Any,
        optifine_api: Any,
        http_client: Any,
        logger: Callable[..., None] | None = None,
        working_directory: Path | str = ".",
    ) -> None:
        self.minecraft_directory = Path(minecraft_directory)
        self.java_runtime = java_runtime
        self.available_java_versions = available_java_versions
        self.launcher_api = launcher_api
        self.optifine_api = optifine_api
        self.http = http_client
        self.logger = logger
        self.working_directory = Path(working_directory)

    def install(
        self,
        loader: str,
        minecraft_version: str,
        callback: dict[str, Callable[..., None]] | None = None,
        neoforge_versions: dict[str, Any] | None = None,
    ) -> bool:
        if not loader or not minecraft_version:
            return False

        callbacks = callback or {}
        java_versions = self.available_java_versions()
        if not java_versions:
            raise RuntimeError("No supported Java runtime versions are available")

        java_major = java_versions[-1]
        java_path = self.java_runtime.get_any_java_exe(java_major)
        if not java_path:
            self._log(f"Installing Java {java_major} runtime")
            self.java_runtime.download_and_extract_java(java_major, callbacks)
            java_path = self.java_runtime.get_any_java_exe(java_major)

        if not java_path:
            raise FileNotFoundError(f"Java {java_major} executable was not found")

        self._log(f"Installing Minecraft {minecraft_version} with {loader}")
        self._log(f"Java executable: {java_path}")

        if loader == "Fabric":
            self.launcher_api.fabric.install_fabric(
                minecraft_version=minecraft_version,
                minecraft_directory=str(self.minecraft_directory),
                callback=callbacks,
                java=java_path,
            )
        elif loader == "Quilt":
            self.launcher_api.quilt.install_quilt(
                minecraft_version=minecraft_version,
                minecraft_directory=str(self.minecraft_directory),
                callback=callbacks,
                java=java_path,
            )
        elif loader == "Forge":
            forge_version = self.launcher_api.forge.find_forge_version(minecraft_version)
            self.launcher_api.forge.install_forge_version(
                forge_version,
                path=str(self.minecraft_directory),
                callback=callbacks,
                java=java_path,
            )
        elif loader == "OptiFine":
            self._install_optifine(minecraft_version, java_path, callbacks)
        elif loader == "NeoForge":
            self.launcher_api.install.install_minecraft_version(
                versionid=minecraft_version,
                minecraft_directory=str(self.minecraft_directory),
                callback=callbacks,
            )
            versions = neoforge_versions or {}
            self.launcher_api.neoforge.download_and_run(
                version=versions[minecraft_version],
                path_minecraft=str(self.minecraft_directory),
                java=java_path,
            )
        elif loader == "Cleanroom":
            self.launcher_api.install.install_minecraft_version(
                versionid="1.12.2",
                minecraft_directory=str(self.minecraft_directory),
                callback=callbacks,
            )
            self.launcher_api.cleanroom.download_and_run(
                version=minecraft_version,
                path_minecraft=str(self.minecraft_directory),
                java=java_path,
            )
        else:
            raise ValueError(f"Unsupported loader: {loader}")

        return True

    def _install_optifine(
        self,
        minecraft_version: str,
        java_path: str,
        callback: dict[str, Callable[..., None]],
    ) -> None:
        self.launcher_api.install.install_minecraft_version(
            versionid=minecraft_version,
            minecraft_directory=str(self.minecraft_directory),
            callback=callback,
        )
        versions = self.optifine_api.getVersion(mc_version=minecraft_version)
        download_url = versions[minecraft_version][0]["url"]
        response = self.http.get(download_url)
        response.raise_for_status()

        bridge_directory = self.working_directory / "ofb"
        bridge_directory.mkdir(parents=True, exist_ok=True)
        optifine_archive = bridge_directory / "Optifine.jar"
        optifine_archive.write_bytes(response.content)
        command = (
            f'"{java_path}" -jar "{self.working_directory / "Bridge.jar"}" '
            f'"{self.minecraft_directory}" -log=console > optifine.log 2>&1'
        )
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=self.working_directory,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        process.wait()
        optifine_archive.unlink(missing_ok=True)

    def _log(self, message: str, level: str = "INFO") -> None:
        if self.logger is not None:
            self.logger(message, level=level)
