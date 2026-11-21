import os
import re
from pathlib import Path
from typing import Any, Callable


class MinecraftLaunchService:
    def __init__(
        self,
        minecraft_directory: Path | str,
        launcher_directory: Path | str,
        launcher_api: Any,
        java_runtime: Any,
        online: bool,
        logger: Callable[..., None] | None = None,
    ) -> None:
        self.minecraft_directory = Path(minecraft_directory)
        self.launcher_directory = Path(launcher_directory)
        self.launcher_api = launcher_api
        self.java_runtime = java_runtime
        self.online = online
        self.logger = logger

    def build_command(
        self,
        selected_version: str,
        work_folder: str | Path,
        username: str,
        uuid: str,
        memory_megabytes: str,
        custom_arguments: list[str],
        java_choice: str,
        check_java: bool,
        use_ely_by: bool,
        callback: dict[str, Callable[..., None]] | None = None,
    ) -> tuple[list[str], dict[str, Any]]:
        jvm_arguments = [
            f"-Xmx{memory_megabytes}M",
            f"-Xms{memory_megabytes}M",
            "-Djavax.net.ssl.trustStoreType=Windows-ROOT",
        ]

        custom_argument_text = " ".join(custom_arguments)
        if not re.search(r"-XX:\+Use\w+GC", custom_argument_text, re.IGNORECASE) or "-XX:+UseG1GC" in custom_arguments:
            jvm_arguments.extend([
                "-XX:+UseG1GC",
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:MaxGCPauseMillis=50",
                "-XX:+DisableExplicitGC",
                "-XX:+ParallelRefProcEnabled",
            ])

        options: dict[str, Any] = {
            "gameDirectory": str(work_folder),
            "username": username,
            "uuid": uuid,
            "jvmArguments": jvm_arguments + list(custom_arguments),
        }

        self._configure_java(
            options,
            selected_version,
            java_choice,
            check_java,
            callback,
        )

        if use_ely_by:
            injector_path = self.launcher_directory / "injector.jar"
            options["jvmArguments"].append(f"-javaagent:{injector_path.resolve()}=ely.by")

        log_config_path = (self.launcher_directory / "log4jshell.xml").resolve()
        options["jvmArguments"].extend([
            f"-Dlog4j.configurationFile=file:///{str(log_config_path).replace(os.sep, '/')}",
            "-Dfile.encoding=UTF-8",
        ])

        command = self.launcher_api.command.get_minecraft_command(
            selected_version,
            str(self.minecraft_directory),
            options,
        )
        return command, options

    def _configure_java(
        self,
        options: dict[str, Any],
        selected_version: str,
        java_choice: str,
        check_java: bool,
        callback: dict[str, Callable[..., None]] | None,
    ) -> None:
        if re.match(r"^Java [1-9]\d*$", java_choice):
            java_version = java_choice.split()[1]
            java_path = self.java_runtime.get_any_java_exe(java_version)
            if self.online and check_java:
                self.java_runtime.download_and_extract_java(java_version, callback)
                options["executablePath"] = self.java_runtime.get_any_java_exe(java_version)
            elif java_path:
                options["executablePath"] = java_path
        elif java_choice not in ("Latest", "Stable"):
            options["executablePath"] = java_choice
        elif java_choice == "Latest":
            runtime_info = self.launcher_api.runtime.get_version_runtime_information(
                selected_version,
                str(self.minecraft_directory),
            )
            java_version = runtime_info["javaMajorVersion"]
            java_path = self.java_runtime.get_any_java_exe(java_version)
            if self.online:
                self.java_runtime.download_and_extract_java(java_version, callback)
                options["executablePath"] = self.java_runtime.get_any_java_exe(java_version)
            elif java_path:
                options["executablePath"] = java_path

    def _log(self, message: str, level: str = "INFO") -> None:
        if self.logger is not None:
            self.logger(message, level=level)
