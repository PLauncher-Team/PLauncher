from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


def check_internet_connection() -> float | None:
    start_time = time.perf_counter()

    try:
        with create_connection(("1.1.1.1", 80), timeout=1.0):
            end_time = time.perf_counter()

        ping_ms = (end_time - start_time) * 1000
        return round(ping_ms, 2)

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        log(f"Нет интернета: {error_type} - {error_msg}", "WARNING")
        return 0


def save_config_menu():
    username = username_entry.get()
    if not username:
        username = "Steve"
    LauncherConfig.config["name"] = username
    save_config()


def get_available_memory() -> int:
    total_memory = virtual_memory().total
    total_memory_gb = round(total_memory / (1024 ** 3))
    return total_memory_gb


def open_logs():
    if not os.path.isfile("minecraft.log"):
        ToastNotification(title=language_manager.get("messages.titles.warning"),
                          message=language_manager.get("messages.texts.warning.logs"),
                          toast_type="warning")
    else:
        os.startfile("minecraft.log")


def save_version():
    with open(os.path.join(LaunchOptions.minecraft_path, "version.json"), "w") as ver:
        json.dump(LauncherConfig.version, ver, indent=4)


def save_config():
    with open("data.json", "w") as con:
        json.dump(LauncherConfig.config, con, indent=4)


def set_version(e: str = None):
    if e:
        version_combobox_ctk.set(e)
        LauncherConfig.version["version"] = version_combobox_ctk.get() \
            .replace(language_manager.get("main.types_versions.not_completed"), "") \
            .replace(language_manager.get("main.types_versions.installed"), "")
        save_version()


def create_minecraft_environment():
    dirs = ["assets", "bin", "libraries", "logs", "resourcepacks", "saves",
            "screenshots", "shaderpacks", "versions", "profiles", "mods"]

    for directory in dirs:
        os.makedirs(os.path.join(LaunchOptions.minecraft_path, directory), exist_ok=True)

    data_profile = {
        "profiles": {
            "forge": {
                "name": "forge",
                "lastVersionId": "1.12.2-forge1.12.2-14.23.0.2501"
            }
        },
        "clientToken": "dd76b195-eb71-4786-b561-7ebd985574bf"
    }

    with open(os.path.join(LaunchOptions.minecraft_path, "launcher_profiles.json"), "w") as k:
        json.dump(data_profile, k, indent=4)

    if os.path.isfile(os.path.join(LaunchOptions.minecraft_path, "version.json")):
        with open(os.path.join(LaunchOptions.minecraft_path, "version.json")) as d:
            LauncherConfig.version = json.load(d)

        for a in default_version:
            if a not in LauncherConfig.version:
                LauncherConfig.version[a] = default_version[a]
            with open(os.path.join(LaunchOptions.minecraft_path, "version.json"), "w") as x:
                json.dump(LauncherConfig.version, x, indent=4)
    else:
        with open(os.path.join(LaunchOptions.minecraft_path, "version.json"), "w") as v:
            LauncherConfig.version = default_version
            json.dump(LauncherConfig.version, v, indent=4)


def save_set(var, value):
    LauncherConfig.config[var] = value
    save_config()


def create_memory_options() -> list:
    memory_options = []
    for gb in range(1, LauncherConfig.MAX_MEMORY_GB + 1):
        mb = gb * 1024
        memory_options.append(str(mb))
    return memory_options


def validate_memory(new_value):
    if getattr(memory_combobox, "_programmatic_insert", False) or new_value == "":
        return True

    if not new_value.isdigit():
        return False

    value = int(new_value)

    if value > LauncherConfig.MAX_MEMORY_GB * 1024:
        return False

    if new_value.startswith("0"):
        return False

    on_select(new_value)
    return True


def on_select(value):
    LauncherConfig.config["memory_args"] = value
    save_config()


def entry_input():
    LauncherConfig.config["custom_args"] = args_entry.get()
    save_config()


def change_mine(selection: bool = True):
    if selection:
        folder = filedialog.askdirectory(
            title=language_manager.get("settings.2_page.select_directory")
        ).replace("/", "\\")

        if folder == os.path.join(os.getenv('APPDATA'), ".minecraft"):
            default_directory.toggle()
            change_mine(False)
            folder = ""
    else:
        if default_var.get():
            change_folder.configure(state="disabled")
            folder = os.path.join(os.getenv('APPDATA'), ".minecraft")
            LauncherConfig.config["default_path"] = True
            save_config()
        else:
            change_folder.configure(state="normal")
            folder = LauncherConfig.config["mine_path"]
            LauncherConfig.config["default_path"] = False
            save_config()

    if folder:
        LaunchOptions.minecraft_path = folder
        current_folder.configure(
            text=language_manager.get('settings.2_page.current_path') + LaunchOptions.minecraft_path)

        create_minecraft_environment()

        if not default_var.get():
            LauncherConfig.config["mine_path"] = LaunchOptions.minecraft_path
            save_config()

        root.after_idle(load_versions)
        list_profiles.configure(values=list_dir())
        if LauncherConfig.version["profile"]:
            list_profiles.set(LauncherConfig.version["profile"])
        else:
            list_profiles.set(language_manager.get("settings.4_page.no"))
        mod_viewer_window._first_load_done = False
        log(f"Директория Minecraft изменена на: {LaunchOptions.minecraft_path}")


def del_installed_version():
    currents = installed_versions_combobox_ctk.get()
    if not currents:
        return

    new_message(
        title=language_manager.get("messages.titles.warning"),
        message=f"{language_manager.get('messages.texts.warning.delete_game_version')} ({currents})",
        icon="question",
        option_1=language_manager.get("messages.answers.no"),
        option_2=language_manager.get("messages.answers.yes")
    )

    if GuiOptions.msg.get() == language_manager.get("messages.answers.yes"):
        log(f"Удаление версии: {currents}")
        for current in currents.split():
            shutil.rmtree(os.path.join(LaunchOptions.minecraft_path, "versions", current))
            for i in ("download", "not_comp"):
                if current in LauncherConfig.version[i]:
                    LauncherConfig.version[i].remove(current)
        save_version()
        root.after_idle(load_versions)


def kill_thread(thread: threading.Thread):
    if not thread.is_alive():
        return getattr(thread, "_return", None)

    thread_id = thread.ident
    if thread_id is None:
        return getattr(thread, "_return", None)

    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread_id), ctypes.py_object(SystemExit))

    if res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), 0)

    return getattr(thread, "_return", None)
