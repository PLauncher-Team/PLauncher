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

    def test_bind_updates_existing_module_globals(self):
        with tempfile.TemporaryDirectory() as directory:
            modules_directory = Path(directory)
            (modules_directory / "gui.py").write_text(
                "def read_option():\n    return GuiOptions.select_page\n",
                encoding="utf-8",
            )
            runtime = LegacyModuleRuntime(modules_directory, {})
            gui_module = runtime.load("gui")

            class Options:
                select_page = "settings"

            runtime.bind("GuiOptions", Options())
            self.assertEqual(gui_module.read_option(), "settings")

    def test_bind_during_module_execution_updates_loading_module(self):
        with tempfile.TemporaryDirectory() as directory:
            modules_directory = Path(directory)
            (modules_directory / "skin.py").write_text(
                "def read_option():\\n    return default_skin_var.get()\\n",
                encoding="utf-8",
            )
            (modules_directory / "gui.py").write_text(
                "default_skin_var = object()\\nlegacy_runtime.bind('default_skin_var', default_skin_var)\\n",
                encoding="utf-8",
            )
            namespace = {}
            runtime = LegacyModuleRuntime(modules_directory, namespace)
            namespace["legacy_runtime"] = runtime
            skin_module = runtime.load("skin")
            gui_module = runtime.load("gui")
            self.assertIs(skin_module.default_skin_var, gui_module.default_skin_var)

    def test_missing_module_raises(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = LegacyModuleRuntime(directory, {})
            with self.assertRaises(ModuleNotFoundError):
                runtime.load("missing")


if __name__ == "__main__":
    unittest.main()
