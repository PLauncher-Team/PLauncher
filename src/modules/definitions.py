class LaunchOptions:
    is_running = False
    minecraft_process = None
    loader_process = None
    step = None
    progress = None
    total_files = 0
    versions = []
    old_types_versions = []
    minecraft_log_file = None

class LauncherConfig:
    ping = check_internet_connection()
    IS_INTERNET = bool(ping)
    CURRENT_VERSION = "v1.0.1"
    FPS = get_refresh_rate()
    MAX_MEMORY_GB = get_available_memory()

