import json
import tempfile
import unittest
from pathlib import Path

from src.plauncher.services.translation import TranslationService


class TranslationServiceTests(unittest.TestCase):
    def test_loads_nested_translations(self):
        with tempfile.TemporaryDirectory() as directory:
            locales = Path(directory)
            (locales / "en.json").write_text(
                json.dumps({"language": "English", "messages": {"ready": "Ready"}}),
                encoding="utf-8",
            )
            service = TranslationService(locales, language="en")
            self.assertEqual(service.get("messages.ready"), "Ready")
            self.assertEqual(service.get_languages_names(), {"en": "English"})

    def test_falls_back_to_first_supported_language(self):
        with tempfile.TemporaryDirectory() as directory:
            locales = Path(directory)
            (locales / "en.json").write_text(
                json.dumps({"language": "English"}),
                encoding="utf-8",
            )
            service = TranslationService(locales, language="missing")
            self.assertEqual(service.language, "en")

    def test_detects_language_and_persists_it(self):
        with tempfile.TemporaryDirectory() as directory:
            locales = Path(directory)
            (locales / "ru.json").write_text(
                json.dumps({"language": "Русский"}),
                encoding="utf-8",
            )
            settings = {}
            saved = []
            service = TranslationService(
                locales,
                settings=settings,
                save_settings=lambda: saved.append(True),
                locale_provider=lambda: ("ru_RU", "UTF-8"),
            )
            self.assertEqual(service.language, "ru")
            self.assertEqual(settings["language"], "ru")
            self.assertEqual(saved, [True])


if __name__ == "__main__":
    unittest.main()
