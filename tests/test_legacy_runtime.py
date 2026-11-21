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
                "result = SharedValue.value + injected_value\n",
                encoding="utf-8",
            )
            namespace = {"injected_value": 8}
            runtime = LegacyModuleRuntime(modules_directory, namespace)
            runtime.load_many(["first", "second"])
            self.assertEqual(runtime.modules["second"].result, 50)
            runtime.bind("injected_value", 10)
            self.assertEqual(runtime.modules["first"].injected_value, 10)
            self.assertEqual(runtime.modules["second"].injected_value, 10)

    def test_missing_module_raises(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = LegacyModuleRuntime(directory, {})
            with self.assertRaises(ModuleNotFoundError):
                runtime.load("missing")


if __name__ == "__main__":
    unittest.main()
