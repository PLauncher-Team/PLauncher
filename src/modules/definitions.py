from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *

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
    ping = check_internet_connection()
    IS_INTERNET = bool(ping)
    CURRENT_VERSION = "v1.1"
    FPS = get_refresh_rate()
    MAX_MEMORY_GB = get_available_memory()
    USER_AGENT = f"PLauncher-Team/PLauncher/{CURRENT_VERSION}"
    version = {}
    config = {}

class GuiOptions:
    def __init__(self):
        self.msg = None
        self.hover_color = ctk.ThemeManager.theme["CTkButton"]["hover_color"][1]
        self.fg_color = ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1]
        self.select_page = None

class LoadersVersions:
    dictionary_neoforge = {}
    forge_versions_mine = []
    neoforge_versions_mine = []
    fabric_versions_mine = []
    quilt_versions_mine = []
    optifine_version_mine = []
    loaders_versions_mine = {
        "Fabric": fabric_versions_mine,
        "Forge": forge_versions_mine,
        "Quilt": quilt_versions_mine,
        "OptiFine": optifine_version_mine,
        "NeoForge": neoforge_versions_mine,
    }