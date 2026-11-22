from typing import Any

from . import ui_support
from .ui_support import *
from .ui import assembly
from .ui.mods import manager, view
from .ui.notifications import ToastNotification, new_message
from .ui.mods.manager import ModManager
from .ui.mods.view import ModViewer

def configure(**dependencies: Any) -> None:
    for module in (ui_support, assembly, manager, view):
        module.configure(**dependencies)
    ui_support.configure(new_message=new_message)

def initialize_gui() -> dict[str, Any]:
    created = assembly.initialize_gui()
    configure(**created)
    return created

