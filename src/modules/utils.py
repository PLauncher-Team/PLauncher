def check_internet_connection() -> bool:
    """Check internet connection by attempting to connect to Cloudflare DNS server."""
    try:
        create_connection(("1.1.1.1", 53), timeout=1)
        return True
    except Exception:
        return False


def save_config_menu():
    """Save username configuration from the settings menu."""
    username = username_entry.get()
    if not username:
        username = "Steve"
    config["name"] = username
    save_config(config)


def get_available_memory() -> int:
    """Get total available system memory in GB."""
    total_memory = virtual_memory().total
    total_memory_gb = round(total_memory / (1024 ** 3))
    return total_memory_gb


def open_logs():
    """Open Minecraft logs file or show warning if not found."""
    if not os.path.isfile("minecraft.log"):
        new_message(title=language_manager.get("messages.titles.warning"),
                    message=language_manager.get("messages.texts.warning.logs"),
                    icon="warning",
                    option_1=language_manager.get("messages.answers.ok"))
    else:
        os.startfile("minecraft.log")


def save_version(val: dict):
    """Save version configuration to version.json file."""
    with open(os.path.join(minecraft_path, "version.json"), "w") as ver:
        json.dump(val, ver, indent=4)


def save_config(val):
    """Save main configuration to data.json file."""
    with open("data.json", "w") as con:
        json.dump(val, con, indent=4)


def create_minecraft_environment(minecraft_path):
    """Create required Minecraft directories and files."""
    global version
    # List of required Minecraft directories
    dirs = ["assets", "bin", "libraries", "logs", "resourcepacks", "saves",
            "screenshots", "shaderpacks", "versions", "profiles", "mods"]

    # Create directories if they don't exist
    for directory in dirs:
        os.makedirs(os.path.join(minecraft_path, directory), exist_ok=True)

    # Default launcher profiles data
    data_profile = {
        "profiles": {
            "forge": {
                "name": "forge",
                "lastVersionId": "1.12.2-forge1.12.2-14.23.0.2501"
            }
        },
        "clientToken": "dd76b195-eb71-4786-b561-7ebd985574bf"
    }

    # Create launcher_profiles.json if doesn't exist
    with open(os.path.join(minecraft_path, "launcher_profiles.json"), "w") as k:
        json.dump(data_profile, k, indent=4)

    # Handle version.json file
    if os.path.isfile(os.path.join(minecraft_path, "version.json")):
        with open(os.path.join(minecraft_path, "version.json")) as d:
            version = json.load(d)
        # Add any missing default values
        for a in default_version:
            if a not in version:
                version[a] = default_version[a]
            with open(os.path.join(minecraft_path, "version.json"), "w") as x:
                json.dump(version, x, indent=4)
    else:
        # Create new version.json with defaults
        with open(os.path.join(minecraft_path, "version.json"), "w") as v:
            version = default_version
            json.dump(version, v, indent=4)


def correct_value(event):
    """Validate memory selection input and update configuration."""
    global previous_value
    value = selected_memory.get()

    # Only allow digits
    if value and not value.isdigit():
        selected_memory.set(previous_value)
    elif value and value[0] == "0":
        selected_memory.set(value[1:])

    previous_value = selected_memory.get()
    on_select()


def save_set(var, value):
    """Save a specific setting to configuration."""
    config[var] = value
    save_config(config)


def create_memory_options() -> list:
    """Create list of memory options based on available system memory."""
    memory_options = []
    for gb in range(1, MAX_MEMORY_GB + 1):
        mb = gb * 1024
        memory_options.append(str(mb))
    return memory_options


def on_select():
    """Handle memory selection change event."""
    global config, previous_value
    previous_value = selected_memory.get()
    config["memory_args"] = previous_value
    save_config(config)


def entry_input():
    """Handle custom JVM arguments input."""
    global config
    config["custom_args"] = args_entry.get()
    save_config(config)


def change_mine(selection: bool=True):
    """Change Minecraft directory path."""
    global minecraft_path, version
    if selection:
        # Show directory selection dialog
        folder = filedialog.askdirectory(
            title=language_manager.get("settings.2_page.select_directory")
        ).replace("/", "\\")

        # Handle default directory case
        if folder == os.path.join(os.getenv('APPDATA'), ".minecraft"):
            default_directory.toggle()
            change_mine(False)
            folder = ""
    else:
        if default_var.get():
            # Use default directory
            change_folder.configure(state="disabled")
            folder = os.path.join(os.getenv('APPDATA'), ".minecraft")
            config["default_path"] = True
            save_config(config)
        else:
            # Use custom directory
            change_folder.configure(state="normal")
            folder = config["mine_path"]
            config["default_path"] = False
            save_config(config)

    if folder:
        minecraft_path = folder
        current_folder.configure(
            text=language_manager.get('settings.2_page.current_path') + minecraft_path)

        # Recreate environment in new location
        create_minecraft_environment(minecraft_path)

        if not default_var.get():
            config["mine_path"] = minecraft_path
            save_config(config)

        # Refresh UI elements
        root.after(0, load_versions)
        list_profiles.configure(values=list_dir())
        if version["profile"]:
            list_profiles.set(version["profile"])
        else:
            list_profiles.set(language_manager.get("settings.4_page.no"))


def del_installed_version():
    """Delete an installed Minecraft version."""
    currents = installed_versions_combobox_ctk.get()
    if not currents:
        return

    # Show confirmation dialog
    new_message(
        title=language_manager.get("messages.titles.warning"),
        message=f"{language_manager.get('messages.texts.warning.delete_game_version')} ({currents})",
        icon="question",
        option_1=language_manager.get("messages.answers.no"),
        option_2=language_manager.get("messages.answers.yes")
    )

    if msg.get() == language_manager.get("messages.answers.yes"):
        # Remove version directory and update configuration
        for current in currents.split():
            shutil.rmtree(os.path.join(minecraft_path, "versions", current))
            for i in ("download", "not_comp"):
                if current in version[i]:
                    version[i].remove(current)
        save_version(version)
        root.after(0, load_versions)


def kill_thread(thread: threading.Thread):
    """Forcefully terminate a thread."""
    if not thread.is_alive():
        return getattr(thread, "_return", None)

    thread_id = thread.ident
    if thread_id is None:
        return getattr(thread, "_return", None)

    # Use ctypes to send async exception to thread
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread_id), ctypes.py_object(SystemExit))

    if res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), 0)

    return getattr(thread, "_return", None)