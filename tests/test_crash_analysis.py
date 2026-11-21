import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from src.plauncher.services.crash_analysis import CrashLogAnalyzerService


class CrashLogAnalyzerServiceTests(unittest.TestCase):
    def test_uses_pollinations_response_when_available(self):
        http = SimpleNamespace(post=Mock(return_value=SimpleNamespace(
            raise_for_status=Mock(),
            text="Crash cause",
        )))
        service = CrashLogAnalyzerService(http, "test")
        result = service.get_response([
            {"role": "system", "content": "system"},
            {"role": "user", "content": "log"},
        ])
        self.assertEqual(result, "Crash cause")
        http.post.assert_called_once()

    def test_falls_back_to_mclo_after_pollinations_failure(self):
        failed = SimpleNamespace(
            raise_for_status=Mock(side_effect=RuntimeError("offline")),
            text="",
        )
        successful = SimpleNamespace(
            raise_for_status=Mock(),
            json=Mock(return_value={
                "analysis": {
                    "problems": [
                        {"solutions": [{"message": "Update the driver"}]},
                        {"solutions": [{"message": "Remove the incompatible mod"}]},
                    ]
                }
            }),
        )
        http = SimpleNamespace(post=Mock(side_effect=[failed, successful]))
        service = CrashLogAnalyzerService(http, "test")
        result = service.get_response([
            {"role": "system", "content": "system"},
            {"role": "user", "content": "log"},
        ])
        self.assertEqual(result, "Update the driver\nRemove the incompatible mod")
        self.assertEqual(http.post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
