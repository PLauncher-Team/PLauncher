import json
import tempfile
import unittest
from pathlib import Path

from src.plauncher.services.skin import SkinTexturePackService


class SkinTexturePackServiceTests(unittest.TestCase):
    def test_creates_resource_pack_and_updates_options(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skin = root / "skin.png"
            skin.write_bytes(b"skin-data")
            minecraft = root / ".minecraft"
            service = SkinTexturePackService(minecraft, skin)
            pack = service.run()
            self.assertTrue((pack / "pack.mcmeta").is_file())
            self.assertTrue((pack / "assets/minecraft/textures/entity/steve.png").is_file())
            self.assertTrue((pack / "assets/minecraft/textures/entity/player/slim/steve.png").is_file())
            options = (minecraft / "options.txt").read_text(encoding="utf-8")
            self.assertIn('"PLauncher skins"', options)
            self.assertEqual(
                json.loads((pack / "pack.mcmeta").read_text(encoding="utf-8"))["pack"]["pack_format"],
                15,
            )

    def test_missing_skin_fails_before_creating_pack(self):
        with tempfile.TemporaryDirectory() as directory:
            service = SkinTexturePackService(Path(directory) / ".minecraft", Path(directory) / "missing.png")
            with self.assertRaises(FileNotFoundError):
                service.run()


if __name__ == "__main__":
    unittest.main()
