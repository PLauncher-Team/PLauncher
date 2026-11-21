import tempfile
import unittest
from pathlib import Path

from src.plauncher.services.profiles import ProfileService


class ProfileServiceTests(unittest.TestCase):
    def test_create_list_rename_and_delete_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            service = ProfileService(Path(directory) / ".minecraft")
            profile_path = service.create("survival")
            self.assertTrue((profile_path / "mods").is_dir())
            self.assertEqual(service.list_profiles(), ["survival"])
            renamed_path = service.rename("survival", "creative")
            self.assertTrue(renamed_path.is_dir())
            self.assertEqual(service.list_profiles(), ["creative"])
            service.delete("creative")
            self.assertEqual(service.list_profiles(), [])

    def test_rejects_path_traversal_names(self):
        with tempfile.TemporaryDirectory() as directory:
            service = ProfileService(directory)
            with self.assertRaises(ValueError):
                service.create("../outside")

    def test_rejects_duplicate_profiles(self):
        with tempfile.TemporaryDirectory() as directory:
            service = ProfileService(directory)
            service.create("default")
            with self.assertRaises(FileExistsError):
                service.create("default")


if __name__ == "__main__":
    unittest.main()
