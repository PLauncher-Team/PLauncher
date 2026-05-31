from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *

def thread_load_versions():
    """Load Minecraft versions list in a separate thread."""
    if LauncherConfig.IS_INTERNET:
        LaunchOptions.versions = mcl.utils.get_version_list()
        log(f"Version list retrieved: {len(LaunchOptions.versions)} items", source="launcher_core")
    root.after(0, load_versions)


def save_versions_var():
    """Save version filter settings to configuration."""
    LauncherConfig.config["release"]    = release_var.get()
    LauncherConfig.config["snapshot"]   = snapshot_var.get()
    LauncherConfig.config["old_beta"]   = old_beta_var.get()
    LauncherConfig.config["old_alpha"]  = old_alpha_var.get()
    save_config()


def load_versions():
    """Load and display available Minecraft versions based on filters."""
    if LauncherConfig.version["version"]:
        LaunchOptions.latest_version = LauncherConfig.version["version"]

    try:
        # Get installed versions and their IDs
        installed_versions = mcl.utils.get_installed_versions(LaunchOptions.minecraft_path)
        installed_versions_ids = {version['id'] for version in installed_versions}

        # Get version filter settings
        show_release = release_var.get()
        show_snapshot = snapshot_var.get()
        show_old_beta = old_beta_var.get()
        show_old_alpha = old_alpha_var.get()

        LaunchOptions.old_types_versions = [show_release, show_snapshot, show_old_beta, show_old_alpha]

        # Filter versions based on selected types
        filtered_versions = [
            version for version in LaunchOptions.versions
            if (show_release and version['type'] == 'release') or
               (show_snapshot and version['type'] == 'snapshot') or
               (show_old_beta and version['type'] == 'old_beta') or
               (show_old_alpha and version['type'] == 'old_alpha')
        ]

        # Prepare lists of installed and available versions
        installed_versions_list = [version['id'] for version in installed_versions if
                                   version['id'] in installed_versions_ids]
        other_versions_list = [version['id'] for version in filtered_versions if
                               version['id'] not in installed_versions_ids]

        # Update UI elements with version lists
        installed_versions_combobox.configure(values=installed_versions_list)
        installed_versions_combobox_ctk.set(installed_versions_list[0] if installed_versions_list else "")

        # Add status indicators for installed versions
        for i, value_dow in enumerate(installed_versions_list):
            if value_dow in LauncherConfig.version["download"]:
                installed_versions_list[i] += language_manager.get("main.types_versions.installed")
            elif value_dow in LauncherConfig.version["not_comp"]:
                installed_versions_list[i] += language_manager.get("main.types_versions.not_completed")

        version_combobox.configure(values=installed_versions_list + other_versions_list)
    except Exception as e:
        excepthook(*sys.exc_info())
        ToastNotification(title=language_manager.get("messages.titles.error"),
                    message=language_manager.get("messages.texts.error.loading") + str(e),
                    toast_type="error")

    # Set the selected version in UI
    if LaunchOptions.latest_version in LauncherConfig.version["download"]:
        check_version = LaunchOptions.latest_version + language_manager.get("main.types_versions.installed")
    elif LaunchOptions.latest_version in LauncherConfig.version["not_comp"]:
        check_version = LaunchOptions.latest_version + language_manager.get("main.types_versions.not_completed")
    else:
        check_version = LaunchOptions.latest_version

    if check_version not in version_combobox.values:
        version_combobox_ctk.set("")
    else:
        if LaunchOptions.latest_version in LauncherConfig.version["download"]:
            version_combobox_ctk.set(LaunchOptions.latest_version + language_manager.get("main.types_versions.installed"))
        elif LaunchOptions.latest_version in LauncherConfig.version["not_comp"]:
            version_combobox_ctk.set(LaunchOptions.latest_version + language_manager.get("main.types_versions.not_completed"))
        else:
            version_combobox_ctk.set(LaunchOptions.latest_version)

    log("Version list successfully loaded", source="launcher_core")


def stop_action():
    """Stop the running Minecraft process."""
    launch_button.configure(text=language_manager.get("main.status.finalizing"), state="disabled")
    if LaunchOptions.is_running:
        LaunchOptions.minecraft_log_file.close()
        LaunchOptions.is_running = False
        try:
            log("Terminating Minecraft process.", source="launcher_core")
            LaunchOptions.minecraft_process.terminate()
            LaunchOptions.minecraft_process.wait(timeout=5)
            log("Minecraft process terminated gracefully.", source="launcher_core")
        except subprocess.TimeoutExpired:
            log("Timeout expired; killing Minecraft process.", source="launcher_core")
            LaunchOptions.minecraft_process.kill()
            log("Minecraft process killed.", source="launcher_core")


def set_step(value: str):
    """Update the current step in the installation process."""
    LaunchOptions.step = language_manager.get("main.mcl_status." + value)


def set_max_value(max_value: int):
    """Set the maximum value for progress bar."""
    LaunchOptions.total_files = max_value


def fun_progres(progress: int, bar: ctk.CTkProgressBar):
    """Update progress bar value."""
    bar.set(progress / LaunchOptions.total_files)


@rate_limited(period=0.1, calls=1, raise_on_limit=False)
def progress_bar_update(progress: int=None, bar: ctk.CTkProgressBar=None, check: bool=True, status: bool=True):
    """Update progress bar with rate limiting."""
    if check:
        if status:
            set_status(f"{LaunchOptions.step} ({progress}/{LaunchOptions.total_files})")
        fun_progres(progress, bar)


def set_status(status: str):
    """Update status label text."""
    status_label.configure(text=status)


@rate_limited(period=1, calls=2, raise_on_limit=False)
def launch_game():
    """Launch Minecraft game with selected version and settings."""
    crash_window.withdraw()

    # Get selected version and clean status indicators
    selected_version = version_combobox_ctk.get().replace(
        language_manager.get("main.types_versions.not_completed"), "").replace(
        language_manager.get("main.types_versions.installed"), "")
    username = LauncherConfig.config["name"]

    if not selected_version:
        ToastNotification(title=language_manager.get("messages.titles.warning"),
                    message=language_manager.get("messages.texts.warning.version"),
                    toast_type="warning")
        return

    if not LauncherConfig.config["memory_args"]:
        LauncherConfig.config["memory_args"] = default_config["memory_args"]
        selected_memory.set(value=default_config["memory_args"])

    # Prepare UI for launch
    progress_bar.set(0)
    for obj in settings_button, logs_button, feedback_button:
        obj.configure(state="disabled")

    def cancel():
        """Handle launch cancellation."""
        set_status(language_manager.get("main.status.loading_canceled"))
        save_version()
        normal_state()

    def normal_state():
        """Restore UI to normal state after launch attempt."""
        launch_button.configure(text=language_manager.get("main.buttons.launch_game"),
                                command=lambda: threading.Thread(target=launch_game).start(),
                                state="normal")
        for obj in settings_button, logs_button, feedback_button:
            obj.configure(state="normal")
        progress_bar.set(0)

    def run_minecraft():
        """Execute Minecraft process with configured options."""
        try:
            # Clean up old skin resource packs if exists
            if os.path.isdir(os.path.join(LaunchOptions.minecraft_path, "resourcepacks", "PLauncher skins")):
                shutil.rmtree(os.path.join(LaunchOptions.minecraft_path, "resourcepacks", "PLauncher skins"))

            # Handle Ely.by authentication if enabled
            if LauncherConfig.IS_INTERNET and ely_by_var.get() and not default_skin_var.get():
                try:
                    uuid_response = requests.get(
                        fr"https://authserver.ely.by/api/users/profiles/minecraft/{username}",
                        timeout=5)
                    uuid_response.raise_for_status()
                    uuid = uuid_response.json()["id"]
                except Exception as e:
                    excepthook(*sys.exc_info())
                    ToastNotification(title=language_manager.get("messages.titles.error"),
                                message=language_manager.get("messages.texts.error.ely_by_uuid") + str(e),
                                toast_type="error")
                    normal_state()
                    return
            else:
                if username not in LauncherConfig.config:
                    LauncherConfig.config[username] = str(uuid4())
                uuid = LauncherConfig.config[username]

            # Set working directory based on profile
            if LauncherConfig.version["profile"]:
                work_folder = os.path.join(LaunchOptions.minecraft_path, "profiles", "profile_" + LauncherConfig.version["profile"])
            else:
                work_folder = LaunchOptions.minecraft_path

            # Handle custom skin if specified
            if LauncherConfig.config["custom_skin"] and not ely_by_var.get() and not default_skin_var.get():
                MinecraftTexturePackCreator(work_folder, LauncherConfig.config["custom_skin"]).run()
            
            save_config()
            args_custom = args_entry.get().split()

            # Prepare Minecraft launch options
            options = {
                "gameDirectory": work_folder,
                "username": username,
                "uuid": uuid,
                "jvmArguments": args_custom + ["-Xmx" + LauncherConfig.config["memory_args"] + "M",
                                               "-Xms" + str(int(LauncherConfig.config["memory_args"]) // 2) + "M",
                                               "-Djavax.net.ssl.trustStoreType=Windows-ROOT"]
            }

            # Use custom Java path if specified
            if LauncherConfig.config["java"]:
                options["executablePath"] = LauncherConfig.config["java_paths"][LauncherConfig.config["java"]]

            # Add Ely.by agent if enabled
            if LauncherConfig.IS_INTERNET and ely_by_var.get() and not default_skin_var.get():
                options["jvmArguments"].append(rf"-javaagent:{os.path.abspath('injector.jar')}=ely.by")

            # Generate Minecraft launch command
            command = mcl.command.get_minecraft_command(selected_version, LaunchOptions.minecraft_path, options)
            debug_mode = debug_var.get()

            creationflags = 0
            if not debug_mode:
                creationflags = subprocess.CREATE_NO_WINDOW

            # Open log file
            LaunchOptions.minecraft_log_file = open("minecraft.log", "w+", encoding="cp1251", errors="replace")

            # Log launch details
            log("Launching Minecraft\n"
                f"Version: {selected_version}\n"
                f"User: {username}\n"
                f"Args: {', '.join(options['jvmArguments'])}\n"
                f"Java: {command[0]}\n"
                f"Working directory: {work_folder}\n"
                f"Debug: {debug_mode}\n"
                f"UUID: {uuid}",
                source="launcher_core")

            # Create job object to manage process lifetime
            hJob = win32job.CreateJobObject(None, "PLauncher_Job")
            extended_info = win32job.QueryInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation)
            extended_info["BasicLimitInformation"]["LimitFlags"] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            win32job.SetInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation, extended_info)

            # Start Minecraft process
            LaunchOptions.minecraft_process = subprocess.Popen(
                command,
                cwd=work_folder,
                creationflags=creationflags,
                stdout=LaunchOptions.minecraft_log_file,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Assign process to job object
            win32job.AssignProcessToJobObject(hJob, int(LaunchOptions.minecraft_process._handle))

            # Update UI for running state
            if hide_var.get():
                root.withdraw()
            set_status(language_manager.get("main.status.loading_completed"))
            launch_button.configure(text=language_manager.get("main.buttons.complete_game"),
                                    command=stop_action,
                                    state="normal")

            # Wait for process to complete
            LaunchOptions.minecraft_process.wait()

            if hide_var.get():
                root.deiconify()

            # Handle process errors
            if LaunchOptions.is_running and LaunchOptions.minecraft_process.returncode:
                raise Exception(language_manager.get("messages.texts.error.exit_code") + str(LaunchOptions.minecraft_process.returncode))

            normal_state()
            set_status(language_manager.get("main.status.game_completed"))
            LaunchOptions.is_running = False
            LaunchOptions.minecraft_log_file.close()
        except Exception as e:
            excepthook(*sys.exc_info())
            ToastNotification(
                title=language_manager.get("messages.titles.error"),
                message=language_manager.get("messages.texts.error.launch") + str(e),
                toast_type="error"
            )
            normal_state()
            if hide_var.get():
                root.deiconify()
            set_status(language_manager.get("main.status.launch_error"))
            # Show crash window if process failed
            if LaunchOptions.is_running and LaunchOptions.minecraft_process.returncode:
                LaunchOptions.minecraft_log_file.seek(0)
                crash_window.set_log_text(LaunchOptions.minecraft_log_file.read()[-50000:])
                root.after(0, crash_window.open)
            LaunchOptions.is_running = False
            if "log_file" in locals():
                LaunchOptions.minecraft_log_file.close()

    def download_and_run():
        """Download Minecraft files (if needed) and launch the game."""
        if LauncherConfig.IS_INTERNET:
            set_status(language_manager.get("main.status.loading"))
        try:
            if LauncherConfig.IS_INTERNET:
                # Track incomplete downloads
                if selected_version not in LauncherConfig.version["not_comp"]:
                    LauncherConfig.version["not_comp"].append(selected_version)
                    save_version()

                # Download version if not already installed
                if selected_version not in LauncherConfig.version["download"]:
                    log("Downloading Minecraft files...", source="launcher_core")
                    mcl.install.install_minecraft_version(selected_version, LaunchOptions.minecraft_path, callback={
                        "setMax": lambda val_max: set_max_value(val_max),
                        "setProgress": lambda val_prog: progress_bar_update(val_prog, progress_bar),
                        "setStatus": set_step,
                    })
                    log("Minecraft files are ready.", source="launcher_core")

                # Verify files if enabled in settings
                elif check_var.get():
                    log("Verifying Minecraft files...", source="launcher_core")
                    mcl.install.install_minecraft_version(selected_version, LaunchOptions.minecraft_path, callback={
                        "setProgress": lambda val_prog: progress_bar_update(check=False)
                    })
                    log("Minecraft files are ready.", source="launcher_core")

                # Update version status after download
                if selected_version not in LauncherConfig.version["download"]:
                    LauncherConfig.version["download"].append(selected_version)
                    LauncherConfig.version["not_comp"].remove(selected_version)
                    root.after(0, load_versions)

            LaunchOptions.is_running = True
            save_version()
            progress_bar.set(1)
            threading.Thread(target=run_minecraft).start()
        except Exception as e:
            excepthook(*sys.exc_info())
            save_version()
            normal_state()
            ToastNotification(title=language_manager.get("messages.titles.error"),
                        message=language_manager.get("messages.texts.error.loading") + str(e),
                        toast_type="error")
            set_status(language_manager.get("main.status.loading_error"))


    # Start download and launch process in separate thread
    download_thread = threading.Thread(target=download_and_run)
    download_thread.start()

    def off_load():
        """Handle cancellation of download process."""
        launch_button.configure(state="disabled", text=language_manager.get("main.status.finalizing"))
        kill_thread(download_thread)
        cancel()

    launch_button.configure(command=off_load, text=language_manager.get("main.buttons.cancel_loading"))