import unittest

from src.plauncher.models import LaunchSession, LauncherSettings, VersionState


class LauncherSettingsTests(unittest.TestCase):
    def test_round_trip_preserves_settings(self):
        source = {
            "name": "Alex",
            "debug": True,
            "java_paths": ["C:/Java/bin/java.exe"],
            "unknown": "ignored",
        }
        settings = LauncherSettings.from_dict(source)
        self.assertEqual(settings.name, "Alex")
        self.assertTrue(settings.debug)
        self.assertEqual(settings.java_paths, source["java_paths"])
        self.assertNotIn("unknown", settings.to_dict())


class VersionStateTests(unittest.TestCase):
    def test_round_trip_preserves_version_state(self):
        state = VersionState.from_dict({
            "download": ["1.20.4"],
            "not_comp": ["1.21"],
            "version": "1.20.4",
            "profile": "main",
        })
        self.assertEqual(state.to_dict(), {
            "download": ["1.20.4"],
            "not_comp": ["1.21"],
            "version": "1.20.4",
            "profile": "main",
        })


class LaunchSessionTests(unittest.TestCase):
    def test_initial_state_is_stopped(self):
        session = LaunchSession()
        self.assertFalse(session.running)
        self.assertIsNone(session.process)
        self.assertEqual(session.total_files, 0)


if __name__ == "__main__":
    unittest.main()
