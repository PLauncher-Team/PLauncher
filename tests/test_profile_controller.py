import tempfile
import unittest
from pathlib import Path

from src.plauncher.controllers.profiles import ProfileController
from src.plauncher.services.profiles import ProfileService


class FakeLanguageManager:
    def get(self, key):
        return {
            "settings.4_page.no": "No profile",
            "settings.4_page.add": "Add",
            "settings.4_page.delete": "Delete",
            "settings.4_page.save": "Save",
            "settings.4_page.change": "Change",
            "messages.answers.no": "No",
            "messages.answers.yes": "Yes",
            "messages.titles.error": "Error",
            "messages.texts.error.profile_add": "Could not add: ",
            "messages.texts.error.profile_rename": "Could not rename: ",
        }.get(key, key)


class FakeSelector:
    def __init__(self, values, selected):
        self.values = tuple(values)
        self.selected = selected
        self.options = {}

    def get(self):
        return self.selected

    def set(self, value):
        self.selected = value

    def configure(self, **kwargs):
        self.options.update(kwargs)
        if "values" in kwargs:
            self.values = tuple(kwargs["values"])

    def cget(self, name):
        return self.values if name == "values" else self.options.get(name)


class FakeEntry:
    def __init__(self, value=""):
        self.value = value
        self.visible = False

    def get(self):
        return self.value

    def delete(self, *_args):
        self.value = ""

    def insert(self, _index, value):
        self.value = value

    def lift(self):
        self.visible = True

    def lower(self):
        self.visible = False


class FakeButton:
    def __init__(self):
        self.options = {}

    def configure(self, **kwargs):
        self.options.update(kwargs)


class ProfileControllerTests(unittest.TestCase):
    def make_controller(self, directory, confirm_delete=lambda _name: True):
        service = ProfileService(directory)
        service.create("Main")
        selector = FakeSelector(("No profile", "Main"), "Main")
        entry = FakeEntry()
        state = {"active": "Main"}
        events = {"saves": 0, "refreshes": 0, "logs": [], "errors": [], "opened": []}
        controller = ProfileController(
            profile_service=service,
            language_manager=FakeLanguageManager(),
            profile_selector=selector,
            name_entry=entry,
            add_button=FakeButton(),
            delete_button=FakeButton(),
            rename_button=FakeButton(),
            open_button=FakeButton(),
            get_active_profile=lambda: state["active"],
            set_active_profile=lambda value: state.__setitem__("active", value),
            save_active_profile=lambda: events.__setitem__("saves", events["saves"] + 1),
            confirm_delete=confirm_delete,
            notify_error=lambda title, message: events["errors"].append((title, message)),
            refresh_mod_viewer=lambda: events.__setitem__("refreshes", events["refreshes"] + 1),
            logger=lambda message, **kwargs: events["logs"].append((message, kwargs)),
            open_path=events["opened"].append,
        )
        return controller, service, selector, entry, state, events

    def test_select_rename_and_open_profile_use_injected_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            controller, service, selector, entry, state, events = self.make_controller(directory)

            controller.select_profile("Main")
            self.assertEqual(state["active"], "Main")
            self.assertEqual(events["refreshes"], 1)

            entry.value = "Renamed"
            controller.rename_profile("Main")
            self.assertTrue(service.profile_path("Renamed").is_dir())
            self.assertEqual(selector.get(), "Renamed")
            self.assertEqual(state["active"], "Renamed")

            controller.open_folder()
            self.assertEqual(events["opened"], [service.profile_path("Renamed")])

    def test_delete_requires_confirmation_and_resets_active_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            decisions = iter((False, True))
            controller, service, selector, _entry, state, _events = self.make_controller(
                directory, lambda _name: next(decisions)
            )

            controller.delete_current()
            self.assertTrue(service.profile_path("Main").is_dir())
            controller.delete_current()

            self.assertFalse(service.profile_path("Main").exists())
            self.assertEqual(state["active"], False)
            self.assertEqual(selector.get(), "No profile")

    def test_invalid_profile_creation_reports_error_and_restores_no_state(self):
        with tempfile.TemporaryDirectory() as directory:
            controller, _service, _selector, entry, _state, events = self.make_controller(directory)
            entry.value = "../bad"

            controller.save_new_profile()

            self.assertEqual(events["errors"][0][0], "Error")
            self.assertIn("invalid characters", events["errors"][0][1])


if __name__ == "__main__":
    unittest.main()
