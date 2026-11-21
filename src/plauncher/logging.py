import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class LauncherLogger:
    def __init__(self, path: Path, level: int = logging.INFO) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("plauncher")
        self.logger.setLevel(level)
        self.logger.propagate = False
        if not self.logger.handlers:
            handler = RotatingFileHandler(
                path,
                maxBytes=2_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s │ %(levelname)-7s │ %(threadName)-10s │ %(name)s │ %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            self.logger.addHandler(handler)

    def info(self, message: str, *args: object) -> None:
        self.logger.info(message, *args)

    def warning(self, message: str, *args: object) -> None:
        self.logger.warning(message, *args)

    def error(self, message: str, *args: object, exc_info: bool = False) -> None:
        self.logger.error(message, *args, exc_info=exc_info)

    def exception(self, message: str, *args: object) -> None:
        self.logger.exception(message, *args)
