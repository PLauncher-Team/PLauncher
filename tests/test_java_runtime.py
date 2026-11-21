import tempfile
import unittest
from pathlib import Path

from src.plauncher.services.java_runtime import JavaRuntimeService


class JavaRuntimeServiceTests(unittest.TestCase):
    def test_offline_versions_use_supported_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            service = JavaRuntimeService(directory, "test", False, object())
            self.assertEqual(service.get_available_major_versions(), [8, 11, 17, 21, 25])

    def test_semantic_version_is_saved_and_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            service = JavaRuntimeService(directory, "test", False, object())
            target = Path(directory) / "runtime" / "Java 21"
            service.save_local_semantic_version(target, "21.0.2")
            self.assertEqual(service.get_local_semantic_version(target), "21.0.2")

    def test_java_executable_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            service = JavaRuntimeService(directory, "test", False, object())
            executable = Path(directory) / "runtime" / "Java 21" / "bin" / "java.exe"
            executable.parent.mkdir(parents=True)
            executable.touch()
            self.assertEqual(service.get_any_java_exe(21), str(executable.resolve()))
            self.assertEqual(service.get_all_javas_exe(), [str(executable.resolve())])


if __name__ == "__main__":
    unittest.main()
