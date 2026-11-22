import unittest

from src.plauncher.controllers.loaders import LoaderController


class FakeWidget:
    def __init__(self, value="", values=()):
        self.value = value
        self.values = tuple(values)
        self.options = {}
        self.progress = None

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

    def configure(self, **kwargs):
        self.options.update(kwargs)
        if "values" in kwargs:
            self.values = tuple(kwargs["values"])

    def cget(self, name):
        return self.values if name == "values" else self.options.get(name)

    def set_progress(self, value):
        self.progress = value

    def after_idle(self, callback):
        callback()


class FakeDropdown:
    def __init__(self):
        self.values = ()

    def configure(self, **kwargs):
        if "values" in kwargs:
            self.values = tuple(kwargs["values"])


class FakeCatalog:
    def fetch(self, name):
        return [f"{name}-version"], {"metadata": name}


class FakeInstaller:
    def __init__(self):
        self.arguments = None

    def install(self, *args, **kwargs):
        self.arguments = (args, kwargs)


class FakeLanguageManager:
    def get(self, key):
        return key


class LoaderControllerTests(unittest.TestCase):
    def make_controller(self, online=True):
        self.version_selector = FakeWidget("1.20", values=("1.20",))
        self.version_dropdown = FakeDropdown()
        self.loader_selector = FakeWidget("Fabric", values=("Fabric",))
        self.progress = FakeWidget()
        self.install_button = FakeWidget()
        self.launch_button = FakeWidget()
        self.settings_frame = FakeWidget()
        self.installer = FakeInstaller()
        self.progress_updates = []
        self.errors = []
        controller = LoaderController(
            online=online,
            catalog=FakeCatalog(),
            installer=self.installer,
            version_selector=self.version_selector,
            version_dropdown=self.version_dropdown,
            loader_selector=self.loader_selector,
            progress_bar=self.progress,
            install_button=self.install_button,
            launch_button=self.launch_button,
            settings_frame=self.settings_frame,
            language_manager=FakeLanguageManager(),
            logger=lambda *_args, **_kwargs: None,
            notify_error=lambda title, message: self.errors.append((title, message)),
            set_maximum=lambda value: None,
            update_progress=lambda value, bar, status: self.progress_updates.append(
                (value, bar, status)
            ),
            reload_versions=lambda: None,
            current_process=lambda: None,
            kill_thread=lambda _thread: None,
        )
        return controller

    def test_lists_loaded_versions_and_updates_selection(self):
        controller = self.make_controller()
        controller.versions["Fabric"] = ["fabric-1", "fabric-2"]

        self.assertEqual(controller.list_versions("Fabric"), ["fabric-1", "fabric-2"])
        self.assertEqual(self.version_selector.value, "fabric-1")
        self.assertEqual(self.version_dropdown.values, ("fabric-1", "fabric-2"))

    def test_install_uses_selected_loader_and_reloads_versions(self):
        controller = self.make_controller()
        controller.neoforge_versions = {"1.20": {"id": "metadata"}}

        controller.install_selected()

        arguments, options = self.installer.arguments
        self.assertEqual(arguments, ("Fabric", "1.20"))
        self.assertEqual(options["neoforge_versions"], {"1.20": {"id": "metadata"}})

    def test_catalog_load_populates_loader_and_version_controls(self):
        controller = self.make_controller()
        self.loader_selector.value = ""

        controller._load_catalog("Forge")

        self.assertEqual(self.loader_selector.values, ("Fabric", "Forge"))
        self.assertEqual(self.version_dropdown.values, ("Forge-version",))
        self.assertEqual(controller.versions["Forge"], ["Forge-version"])


if __name__ == "__main__":
    unittest.main()
