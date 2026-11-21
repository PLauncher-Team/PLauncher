import tempfile
import unittest
from pathlib import Path

from src.plauncher.legacy import LegacyModuleRuntime


class LegacyModuleRuntimeTests(unittest.TestCase):
    def test_modules_share_injected_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            modules_directory = Path(directory)
            (modules_directory / "first.py").write_text(
                "class SharedValue:\n    value = 42\n",
                encoding="utf-8",
            )
            (modules_directory / "second.py").write_text(
                "result = SharedValue.value\n",
                encoding="utf-8",
            )
            namespace = {}
            runtime = LegacyModuleRuntime(modules_directory, namespace)
            runtime.load_many(["first", "second"])
            self.assertEqual(runtime.modules["second"].result, 42)
            self.assertIs(runtime.modules["second"].SharedValue, namespace["SharedValue"])

    def test_missing_module_raises(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = LegacyModuleRuntime(directory, {})
            with self.assertRaises(ModuleNotFoundError):
                runtime.load("missing")


if __name__ == "__main__":
    unittest.main()
