from typing import Any, Callable


class LoaderCatalogService:
    def __init__(
        self,
        launcher_api: Any,
        optifine_api: Any,
        version_parser: Callable[[str], Any],
        logger: Callable[..., None] | None = None,
    ) -> None:
        self.launcher_api = launcher_api
        self.optifine_api = optifine_api
        self.version_parser = version_parser
        self.logger = logger

    def fetch(self, loader: str) -> tuple[list[str], dict[str, Any]]:
        metadata: dict[str, Any] = {}
        if loader == "Forge":
            versions = self._fetch_forge()
        elif loader == "Fabric":
            versions = [
                item["version"]
                for item in self.launcher_api.fabric.get_all_minecraft_versions()
            ]
        elif loader == "NeoForge":
            metadata = self.launcher_api.neoforge.get_versions()
            versions = sorted(metadata.keys(), reverse=True)
        elif loader == "OptiFine":
            versions = list(self.optifine_api.getVersionList())
        elif loader == "Quilt":
            versions = [
                item["version"]
                for item in self.launcher_api.quilt.get_all_minecraft_versions()
            ]
        elif loader == "Cleanroom":
            versions = list(
                self.launcher_api.cleanroom.get_github_tags("CleanroomMC", "Cleanroom")
            )
        else:
            raise ValueError(f"Unsupported loader catalog: {loader}")
        return versions, metadata

    def _fetch_forge(self) -> list[str]:
        unique_versions = {
            version.split("-")[0]
            for version in self.launcher_api.forge.list_forge_versions()
            if self.version_parser(version.split("-")[0]) >= self.version_parser("1.7.10")
        }
        return sorted(unique_versions, key=self.version_parser, reverse=True)

    def _log(self, message: str, level: str = "INFO") -> None:
        if self.logger is not None:
            self.logger(message, level=level)
