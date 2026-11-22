import unittest

from src.plauncher.controllers.settings import SettingsController


class FakeFrame:
    def __init__(self):
        self.positions = []
        self.after_calls = []
        self.hidden = False

    def place(self, **kwargs):
        self.positions.append(kwargs)

    def place_forget(self):
        self.hidden = True

    def after(self, interval, callback, *args):
        self.after_calls.append((interval, callback, args))

    def bind(self, *_args):
        return None

    def unbind(self, *_args):
        return None


class FakeVariable:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class FakeGuiOptions:
    select_page = None


class FakeRoot:
    def __init__(self):
        self.idle_callbacks = []

    def after_idle(self, callback):
        self.idle_callbacks.append(callback)


class SettingsControllerTests(unittest.TestCase):
    def make_controller(self, fps=60, previous_filters=None):
        self.blackout = FakeFrame()
        self.settings = FakeFrame()
        self.root = FakeRoot()
        self.opacity_calls = []
        self.loaded_versions = []
        self.first_tab = FakeFrame()
        self.second_tab = FakeFrame()
        variables = tuple(FakeVariable(value) for value in (True, False, False, False))
        controller = SettingsController(
            blackout_frame=self.blackout,
            settings_frame=self.settings,
            root=self.root,
            gui_options=FakeGuiOptions(),
            content_frames={"first": self.first_tab, "second": self.second_tab},
            fps=fps,
            opacity_setter=lambda *args, **kwargs: self.opacity_calls.append((args, kwargs)),
            version_filter_vars=variables,
            previous_version_filters=lambda: previous_filters or [True, False, False, False],
            load_versions=lambda: self.loaded_versions.append(True),
        )
        return controller, variables

    def test_zero_fps_still_completes_animation(self):
        controller, _ = self.make_controller(fps=0)
        completed = []

        controller.animate_value(on_complete=lambda: completed.append(True))

        self.assertEqual(len(self.settings.positions), 1)
        self.assertEqual(self.settings.positions[0], {"relx": 1.0})
        interval, callback, args = self.settings.after_calls.pop(0)
        self.assertGreaterEqual(interval, 1)
        callback(*args)
        self.assertEqual(len(self.settings.positions), 2)
        self.assertEqual(self.opacity_calls[-1][1]["value"], 0.3)
        self.assertEqual(completed, [True])
        self.assertEqual(self.settings.after_calls, [])

    def test_changed_version_filters_schedule_refresh_after_closing(self):
        controller, variables = self.make_controller(
            previous_filters=[False, False, False, False]
        )
        variables[0].value = True

        controller.close_settings()
        interval, callback, args = self.settings.after_calls[0]
        self.assertGreaterEqual(interval, 1)

        while self.settings.after_calls:
            _, callback, args = self.settings.after_calls.pop(0)
            callback(*args)

        self.assertEqual(len(self.root.idle_callbacks), 1)
        self.root.idle_callbacks[0]()
        self.assertEqual(controller.gui_options.select_page, None)
        self.assertEqual(self.loaded_versions, [True])

    def test_show_tab_updates_selected_frame(self):
        controller, _ = self.make_controller()

        controller.show_tab("first")
        controller.show_tab("second")

        self.assertTrue(self.first_tab.hidden)
        self.assertEqual(self.second_tab.positions[-1], {
            "relx": 0.05,
            "rely": 0.25,
            "relwidth": 0.9,
            "relheight": 0.7,
        })
        self.assertEqual(controller.gui_options.select_page, "second")


if __name__ == "__main__":
    unittest.main()
