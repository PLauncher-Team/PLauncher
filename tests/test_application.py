import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from plauncher.application import ApplicationState, LauncherApplication
from plauncher.config import ConfigStore


class ConfigStoreTests(unittest.TestCase):
    def test_load_creates_defaults_and_merges_new_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            store = ConfigStore(path)
            initial = store.load()
            self.assertEqual(initial["name"], "Steve")
            self.assertTrue(path.is_file())
            store.save({"name": "Alex"})
            loaded = store.load()
            self.assertEqual(loaded["name"], "Alex")
            self.assertIn("java_paths", loaded)


class LauncherApplicationTests(unittest.TestCase):
    def test_initialization_and_shutdown_lifecycle(self):
        with tempfile.TemporaryDirectory() as directory:
            application = LauncherApplication(directory)
            events = []
            application.add_startup_step(lambda services: events.append("startup"))
            application.add_shutdown_step(lambda services: events.append("shutdown"))
            services = application.initialize()
            self.assertEqual(application.state, ApplicationState.READY)
            self.assertTrue(services.paths.root.is_dir())
            application.run(lambda: events.append("run"))
            self.assertEqual(events, ["startup", "run", "shutdown"])
            self.assertEqual(application.state, ApplicationState.STOPPED)

    def test_startup_failure_marks_application_failed(self):
        with tempfile.TemporaryDirectory() as directory:
            application = LauncherApplication(directory)
            application.add_startup_step(lambda services: (_ for _ in ()).throw(ValueError("failure")))
            with self.assertRaises(ValueError):
                application.initialize()
            self.assertEqual(application.state, ApplicationState.FAILED)


if __name__ == "__main__":
    unittest.main()
