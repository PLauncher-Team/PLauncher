import tempfile
import unittest
from pathlib import Path

from src.plauncher.settings import LauncherSettingsService


class LauncherSettingsServiceTests(unittest.TestCase):
    def test_loads_defaults_and_resets_missing_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service = LauncherSettingsService(
                config_path=root / "data.json",
                minecraft_directory=root / ".minecraft",
                memory_megabytes=3072,
                logger=lambda *_args: None,
            )
            config, existed = service.load_config(root / "themes")
            self.assertFalse(existed)
            self.assertEqual(config["memory_args"], "3072")

            config["custom_image"] = str(root / "missing.png")
            service.save_config()
            loaded, existed = service.load_config(root / "themes")
            self.assertTrue(existed)
            self.assertEqual(loaded["custom_image"], "")

    def test_version_store_follows_selected_minecraft_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service = LauncherSettingsService(
                config_path=root / "data.json",
                minecraft_directory=root / "first",
                memory_megabytes=2048,
                logger=lambda *_args: None,
            )
            version, existed = service.load_version(root / "second")
            self.assertFalse(existed)
            self.assertEqual(version["version"], "")
            self.assertEqual(service.version_store.path, root / "second" / "version.json")


if __name__ == "__main__":
    unittest.main()
