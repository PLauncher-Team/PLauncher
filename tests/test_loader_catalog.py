import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from packaging.version import Version

from src.plauncher.services.loader_catalog import LoaderCatalogService


class LoaderCatalogServiceTests(unittest.TestCase):
    def test_fetches_and_sorts_forge_versions(self):
        launcher_api = SimpleNamespace(
            forge=SimpleNamespace(list_forge_versions=Mock(return_value=[
                "1.20.4-forge-1",
                "1.18.2-forge-2",
                "1.6.4-forge-3",
                "1.20.4-forge-4",
            ]))
        )
        service = LoaderCatalogService(launcher_api, object(), Version)
        versions, metadata = service.fetch("Forge")
        self.assertEqual(versions, ["1.20.4", "1.18.2"])
        self.assertEqual(metadata, {})

    def test_neoforge_catalog_retains_version_metadata(self):
        metadata = {"1.21.1": {"installer": "one"}, "1.20.6": {"installer": "two"}}
        launcher_api = SimpleNamespace(
            neoforge=SimpleNamespace(get_versions=Mock(return_value=metadata))
        )
        service = LoaderCatalogService(launcher_api, object(), Version)
        versions, result_metadata = service.fetch("NeoForge")
        self.assertEqual(versions, ["1.21.1", "1.20.6"])
        self.assertEqual(result_metadata, metadata)

    def test_unknown_catalog_is_rejected(self):
        service = LoaderCatalogService(object(), object(), Version)
        with self.assertRaises(ValueError):
            service.fetch("Unknown")


if __name__ == "__main__":
    unittest.main()
