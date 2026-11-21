import json
import tempfile
import unittest
from pathlib import Path

from src.plauncher.services.environment import MinecraftEnvironmentService


class MinecraftEnvironmentServiceTests(unittest.TestCase):
    def test_ensure_creates_runtime_directories_and_profile_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / ".minecraft"
            service = MinecraftEnvironmentService(root)
            result = service.ensure()
            self.assertEqual(result, root)
            for name in service.DIRECTORIES:
                self.assertTrue((root / name).is_dir())
            profile_file = root / "launcher_profiles.json"
            self.assertTrue(profile_file.is_file())
            data = json.loads(profile_file.read_text(encoding="utf-8"))
            self.assertIn("forge", data["profiles"])


if __name__ == "__main__":
    unittest.main()
