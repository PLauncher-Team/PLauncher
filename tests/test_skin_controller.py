import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.plauncher.controllers.skin import MinecraftSkinRenderer, SkinController


class FakeWidget:
    def __init__(self):
        self.options = {}
        self.image = None
        self.updates = 0

    def configure(self, **kwargs):
        self.options.update(kwargs)
        if "image" in kwargs:
            self.image = kwargs["image"]

    def update_idletasks(self):
        self.updates += 1


class FakeVariable:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class FakeLanguageManager:
    def get(self, key):
        return key


class SkinControllerTests(unittest.TestCase):
    def make_controller(self, settings, online=False):
        self.label = FakeWidget()
        self.update_button = FakeWidget()
        self.select_button = FakeWidget()
        self.ely_checkbox = FakeWidget()
        self.errors = []
        self.logs = []
        controller = SkinController(
            settings=settings,
            default_skin="",
            online=online,
            username=lambda: "Steve",
            skin_label=self.label,
            update_button=self.update_button,
            select_button=self.select_button,
            ely_by_checkbox=self.ely_checkbox,
            default_skin_variable=FakeVariable(settings["default_skin"]),
            ely_by_variable=FakeVariable(settings["ely_by"]),
            language_manager=FakeLanguageManager(),
            http_client=None,
            file_dialog=None,
            image_factory=lambda image: (image.size, image.getpixel((0, 0))),
            notify_error=lambda title, message: self.errors.append((title, message)),
            logger=lambda message, **kwargs: self.logs.append((message, kwargs)),
            save_config=lambda: None,
        )
        return controller

    def test_renderer_returns_scaled_front_view_and_rejects_invalid_dimensions(self):
        rendered = MinecraftSkinRenderer(Image.new("RGBA", (64, 64)), 216).render()
        self.assertEqual(rendered.size, (108, 216))

        with self.assertRaises(ValueError):
            MinecraftSkinRenderer(Image.new("RGBA", (32, 32)), 216).render()

    def test_invalid_custom_skin_resets_setting_and_reports_error(self):
        with tempfile.TemporaryDirectory() as directory:
            skin_path = Path(directory) / "bad.png"
            Image.new("RGBA", (32, 32)).save(skin_path)
            settings = {
                "default_skin": False,
                "ely_by": False,
                "custom_skin": str(skin_path),
            }
            controller = self.make_controller(settings)

            controller.set_skin()

            self.assertEqual(settings["custom_skin"], "")
            self.assertEqual(self.label.image, None)
            self.assertEqual(self.errors, [
                ("messages.titles.error", "messages.texts.error.skin_load")
            ])
            self.assertEqual(self.update_button.options["state"], "normal")


if __name__ == "__main__":
    unittest.main()
