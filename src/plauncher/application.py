from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from .config import ConfigStore, VersionStore
from .logging import LauncherLogger
from .models import LaunchSession, LauncherSettings, VersionState
from .paths import AppPaths
from .services import MinecraftEnvironmentService


class ApplicationState(Enum):
    CREATED = auto()
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAILED = auto()


@dataclass(slots=True)
class ApplicationServices:
    paths: AppPaths
    logger: LauncherLogger
    settings: ConfigStore
    version_settings: VersionStore
    environment: MinecraftEnvironmentService
    session: LaunchSession = field(default_factory=LaunchSession)
    settings_data: LauncherSettings = field(default_factory=LauncherSettings)
    version_data: VersionState = field(default_factory=VersionState)


class LauncherApplication:
    def __init__(
        self,
        root: Path | str,
        minecraft_directory: Path | str | None = None,
    ) -> None:
        paths = AppPaths.from_root(root, minecraft_directory)
        paths.ensure_directories()
        logger = LauncherLogger(paths.logs)
        self.services = ApplicationServices(
            paths=paths,
            logger=logger,
            settings=ConfigStore(paths.config_file),
            version_settings=VersionStore(paths.minecraft_default / "version.json"),
            environment=MinecraftEnvironmentService(paths.minecraft_default),
        )
        self.state = ApplicationState.CREATED
        self._startup_steps: list[Callable[[ApplicationServices], None]] = []
        self._shutdown_steps: list[Callable[[ApplicationServices], None]] = []

    def add_startup_step(self, step: Callable[[ApplicationServices], None]) -> None:
        if self.state is not ApplicationState.CREATED:
            raise RuntimeError("Startup steps can only be registered before initialization")
        self._startup_steps.append(step)

    def add_shutdown_step(self, step: Callable[[ApplicationServices], None]) -> None:
        if self.state in {ApplicationState.STOPPING, ApplicationState.STOPPED}:
            raise RuntimeError("Shutdown has already started")
        self._shutdown_steps.append(step)

    def initialize(self) -> ApplicationServices:
        if self.state is not ApplicationState.CREATED:
            raise RuntimeError(f"Cannot initialize application from {self.state.name}")
        self.state = ApplicationState.INITIALIZING
        try:
            self.services.paths.ensure_directories()
            self.services.environment.ensure()
            self.services.settings_data = LauncherSettings.from_dict(
                self.services.settings.load()
            )
            self.services.version_data = VersionState.from_dict(
                self.services.version_settings.load()
            )
            for step in self._startup_steps:
                step(self.services)
            self.state = ApplicationState.READY
            self.services.logger.info("Application services initialized")
            return self.services
        except Exception:
            self.state = ApplicationState.FAILED
            self.services.logger.exception("Application initialization failed")
            self.services.logger.close()
            raise

    def run(self, main_loop: Callable[[], None]) -> None:
        if self.state is not ApplicationState.READY:
            raise RuntimeError("Application must be initialized before running")
        self.state = ApplicationState.RUNNING
        try:
            main_loop()
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        if self.state in {ApplicationState.STOPPING, ApplicationState.STOPPED}:
            return
        self.state = ApplicationState.STOPPING
        errors: list[Exception] = []
        for step in reversed(self._shutdown_steps):
            try:
                step(self.services)
            except Exception as error:
                errors.append(error)
                self.services.logger.exception("Application shutdown step failed")
        self.services.logger.close()
        self.state = ApplicationState.STOPPED
        if errors:
            raise RuntimeError(f"Application shutdown failed: {errors[0]}") from errors[0]
