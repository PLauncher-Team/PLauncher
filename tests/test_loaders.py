import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from src.plauncher.services.loaders import LoaderInstallationService


class LoaderInstallationServiceTests(unittest.TestCase):
    def create_service(self):
        java_runtime = SimpleNamespace(
            get_any_java_exe=Mock(return_value="C:/Java/bin/java.exe"),
            download_and_extract_java=Mock(),
        )
        launcher_api = SimpleNamespace(
            fabric=SimpleNamespace(install_fabric=Mock()),
        )
        service = LoaderInstallationService(
            minecraft_directory=tempfile.gettempdir(),
            java_runtime=java_runtime,
            available_java_versions=lambda: [21],
            launcher_api=launcher_api,
            optifine_api=object(),
            http_client=object(),
        )
        return service, java_runtime, launcher_api

    def test_fabric_installation_uses_selected_java(self):
        service, java_runtime, launcher_api = self.create_service()
        result = service.install("Fabric", "1.20.4", callback={})
        self.assertTrue(result)
        launcher_api.fabric.install_fabric.assert_called_once_with(
            minecraft_version="1.20.4",
            minecraft_directory=tempfile.gettempdir(),
            callback={},
            java="C:/Java/bin/java.exe",
        )
        java_runtime.download_and_extract_java.assert_not_called()

    def test_empty_selection_does_not_install(self):
        service, _, launcher_api = self.create_service()
        self.assertFalse(service.install("", "1.20.4"))
        launcher_api.fabric.install_fabric.assert_not_called()

    def test_unknown_loader_is_rejected(self):
        service, _, _ = self.create_service()
        with self.assertRaises(ValueError):
            service.install("Unknown", "1.20.4")


if __name__ == "__main__":
    unittest.main()
