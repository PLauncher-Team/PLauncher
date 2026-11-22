from typing import Any

from . import ui_support
from .ui_support import (
    apply_hover_border,
    check_internet_connection,
    get_available_memory,
    get_refresh_rate,
    thread_load_versions,
)
from .ui import assembly

from .ui.notifications import ToastNotification, new_message

def configure(**dependencies: Any) -> None:
    for module in (ui_support, assembly):
        module.configure(**dependencies)
    ui_support.configure(new_message=new_message)

def initialize_gui() -> dict[str, Any]:
    created = assembly.initialize_gui()
    configure(**created)
    return created

