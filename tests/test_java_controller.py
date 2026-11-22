import unittest

from src.plauncher.controllers.java import JavaController


class FakeLanguageManager:
    def get(self, key):
        return {
            "settings.2_page.latest_java": "Latest Java",
            "settings.2_page.recommended_java": "Recommended Java",
            "settings.2_page.add": "Add Java",
            "settings.2_page.select_java": "Select Java",
            "settings.2_page.java_exe": "Java executable",
            "messages.titles.error": "Error",
            "messages.texts.error.java": "Invalid Java",
        }.get(key, key)


class FakeSelector:
    def __init__(self):
        self.value = "Latest Java"
        self.values = []

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

    def configure(self, **kwargs):
        self.values = kwargs.get("values", self.values)


class FakeJavaRuntime:
    def get_all_javas_exe(self):
        return ["C:/runtime/bin/java.exe"]


class FakeProcessApi:
    CREATE_NO_WINDOW = 0

    def __init__(self):
        self.commands = []

    def run(self, command, **_kwargs):
        self.commands.append(command)
        return type("Result", (), {"returncode": 0})()


class JavaControllerTests(unittest.TestCase):
    def make_controller(self, confirm_delete=lambda _name: True):
        self.settings = {"java": "Latest", "java_paths": ["C:/custom/java.exe"]}
        self.selector = FakeSelector()
        self.process_api = FakeProcessApi()
        self.saved = []
        self.errors = []
        controller = JavaController(
            settings=self.settings,
            java_runtime=FakeJavaRuntime(),
            available_major_versions=lambda: [8, 17],
            launcher_api=None,
            minecraft_directory=lambda: "C:/minecraft",
            language_manager=FakeLanguageManager(),
            java_selector=self.selector,
            file_dialog=type(
                "Dialog", (), {"askopenfilename": lambda *_args, **_kwargs: "C:/new/java.exe"}
            )(),
            process_api=self.process_api,
            save_settings=lambda: self.saved.append(True),
            logger=lambda *_args, **_kwargs: None,
            notify_error=lambda title, message: self.errors.append((title, message)),
            confirm_delete=confirm_delete,
        )
        return controller

    def test_add_java_validates_then_saves_and_refreshes_options(self):
        controller = self.make_controller()

        controller.add_java()

        self.assertEqual(self.settings["java_paths"][-1], "C:/new/java.exe")
        self.assertEqual(len(self.saved), 1)
        self.assertIn("Java 17", self.selector.values)
        self.assertEqual(self.process_api.commands[0], ["C:/new/java.exe", "-version"])

    def test_selection_updates_persisted_choice_and_delete_honors_confirmation(self):
        decisions = iter((False, True))
        controller = self.make_controller(lambda _name: next(decisions))

        controller.on_select_java("Recommended Java")
        self.assertEqual(self.settings["java"], "Stable")

        self.selector.value = "C:/custom/java.exe"
        controller.delete_java()
        self.assertIn("C:/custom/java.exe", self.settings["java_paths"])
        controller.delete_java()
        self.assertNotIn("C:/custom/java.exe", self.settings["java_paths"])
        self.assertEqual(self.settings["java"], "Latest")
        self.assertEqual(self.selector.value, "Latest Java")
        self.assertEqual(len(self.saved), 2)


if __name__ == "__main__":
    unittest.main()
