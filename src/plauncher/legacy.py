import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


class LegacyModuleRuntime:
    def __init__(self, modules_directory: Path | str, namespace: dict[str, Any]) -> None:
        self.modules_directory = Path(modules_directory)
        self.namespace = namespace
        self.modules: dict[str, ModuleType] = {}

    def load(self, module_name: str) -> ModuleType:
        module_path = self.modules_directory / f"{module_name}.py"
        if not module_path.is_file():
            raise ModuleNotFoundError(f"Launcher module not found: {module_path}")

        qualified_name = f"plauncher_legacy.{module_name}"
        specification = importlib.util.spec_from_file_location(qualified_name, module_path)
        if specification is None or specification.loader is None:
            raise ImportError(f"Unable to create module specification: {module_path}")

        module = importlib.util.module_from_spec(specification)
        module.__dict__.update(self._public_namespace())
        sys.modules[qualified_name] = module
        self.modules[module_name] = module
        try:
            specification.loader.exec_module(module)
        except Exception:
            self.modules.pop(module_name, None)
            sys.modules.pop(qualified_name, None)
            raise

        self.namespace.update({
            key: value
            for key, value in module.__dict__.items()
            if not key.startswith("__")
        })
        self._synchronize_namespace()
        return module

    def _public_namespace(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in self.namespace.items()
            if not key.startswith("__")
        }

    def _synchronize_namespace(self) -> None:
        shared_values = self._public_namespace()
        for module in self.modules.values():
            module.__dict__.update(shared_values)

    def bind(self, name: str, value: Any) -> None:
        self.namespace[name] = value
        self._synchronize_namespace()

    def load_many(self, module_names: tuple[str, ...] | list[str]) -> None:
        for module_name in module_names:
            self.load(module_name)
