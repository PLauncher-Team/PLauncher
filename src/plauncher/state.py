class LaunchOptions:
    is_running = False
    minecraft_process = None
    loader_process = None
    step = None
    total_files = 0
    versions = []
    old_types_versions = []
    minecraft_log_file = None
    latest_version = None
    minecraft_path = None
    available_major_versions = []


class LauncherConfig:
    ping = 0.0
    IS_INTERNET = False
    CURRENT_VERSION = "v1.1"
    FPS = 60
    MAX_MEMORY_GB = 1
    USER_AGENT = f"PLauncher-Team/PLauncher/{CURRENT_VERSION}"
    version = {}
    config = {}


class GuiOption:
    def __init__(self) -> None:
        import customtkinter as ctk

        self.msg = None
        self.hover_color = ctk.ThemeManager.theme["CTkButton"]["hover_color"][1]
        self.fg_color = ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1]
        self.select_page = None
