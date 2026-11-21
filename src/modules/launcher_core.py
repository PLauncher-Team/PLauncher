from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


def thread_load_versions():
    if LauncherConfig.IS_INTERNET:
        LaunchOptions.versions = mcl.utils.get_version_list()
        log(f"Список версий получен: {len(LaunchOptions.versions)} элементов")
    root.after_idle(load_versions)


def save_versions_var():
    LauncherConfig.config["release"] = release_var.get()
    LauncherConfig.config["snapshot"] = snapshot_var.get()
    LauncherConfig.config["old_beta"] = old_beta_var.get()
    LauncherConfig.config["old_alpha"] = old_alpha_var.get()
    save_config()


def load_versions():
    try:
        if LauncherConfig.version["version"]:
            LaunchOptions.latest_version = LauncherConfig.version["version"]
        
        installed_versions = mcl.utils.get_installed_versions(LaunchOptions.minecraft_path)
        installed_versions_ids = {version['id'] for version in installed_versions}

        show_release = release_var.get()
        show_snapshot = snapshot_var.get()
        show_old_beta = old_beta_var.get()
        show_old_alpha = old_alpha_var.get()

        LaunchOptions.old_types_versions = [show_release, show_snapshot, show_old_beta, show_old_alpha]

        filtered_versions = [
            version for version in LaunchOptions.versions
            if (show_release and version['type'] == 'release') or
               (show_snapshot and version['type'] == 'snapshot') or
               (show_old_beta and version['type'] == 'old_beta') or
               (show_old_alpha and version['type'] == 'old_alpha')
        ]

        installed_versions_list = [version['id'] for version in installed_versions if
                                   version['id'] in installed_versions_ids]
        other_versions_list = [version['id'] for version in filtered_versions if
                               version['id'] not in installed_versions_ids]

        installed_versions_combobox.configure(values=installed_versions_list)

        for i, value_dow in enumerate(installed_versions_list):
            if value_dow in LauncherConfig.version["download"]:
                installed_versions_list[i] += language_manager.get("main.types_versions.installed")
            elif value_dow in LauncherConfig.version["not_comp"]:
                installed_versions_list[i] += language_manager.get("main.types_versions.not_completed")

        version_combobox.configure(values=installed_versions_list + other_versions_list)

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
    except Exception as e:
        excepthook(*sys.exc_info())
        ToastNotification(master=root, title=language_manager.get("messages.titles.error"),
                          message=language_manager.get("messages.texts.error.loading") + str(e),
                          toast_type="error")

    log("Список версий успешно загружен")


def stop_action():
    launch_button.configure(text=language_manager.get("main.status.finalizing"), state="disabled")
    if LaunchOptions.is_running:
        LaunchOptions.is_running = False
        log("Завершение процесса Minecraft.")
        process_service.stop(
            LaunchOptions.minecraft_process,
            LaunchOptions.minecraft_log_file,
        )
        log("Процесс Minecraft завершён.")


def set_step(value: str):
    LaunchOptions.step = language_manager.get("main.mcl_status." + value)


def set_max_value(max_value: int):
    LaunchOptions.total_files = max_value


def fun_progres(progress: int, bar: ctk.CTkProgressBar):
    bar.set(progress / LaunchOptions.total_files)


@rate_limited(period=0.1, calls=1, raise_on_limit=False)
def progress_bar_update(progress: int = None, bar: ctk.CTkProgressBar = None, status: bool = True):
    if status:
        set_status(f"{LaunchOptions.step} ({progress}/{LaunchOptions.total_files})")
    fun_progres(progress, bar)


def set_status(status: str):
    status_label.configure(text=status)


@rate_limited(period=1, calls=2, raise_on_limit=False)
def launch_game():
    crash_window.withdraw()

    selected_version = version_combobox_ctk.get().replace(
        language_manager.get("main.types_versions.not_completed"), "").replace(
        language_manager.get("main.types_versions.installed"), "")
    username = LauncherConfig.config["name"]

    if not selected_version:
        ToastNotification(master=root, title=language_manager.get("messages.titles.warning"),
                          message=language_manager.get("messages.texts.warning.version"),
                          toast_type="warning")
        return

    if not LauncherConfig.config["memory_args"]:
        LauncherConfig.config["memory_args"] = default_config["memory_args"]
        selected_memory.set(value=default_config["memory_args"])

    progress_bar.set(0)
    for obj in settings_button, logs_button, feedback_button, mods_button:
        obj.configure(state="disabled")

    def cancel():
        set_status(language_manager.get("main.status.loading_canceled"))
        save_version()
        normal_state()

    def normal_state():
        launch_button.configure(text=language_manager.get("main.buttons.launch_game"),
                                command=lambda: threading.Thread(target=launch_game).start(),
                                state="normal")
        for obj in settings_button, logs_button, feedback_button, mods_button:
            obj.configure(state="normal")
        progress_bar.set(0)

    def run_minecraft():
        try:
            if os.path.isdir(os.path.join(LaunchOptions.minecraft_path, "resourcepacks", "PLauncher skins")):
                shutil.rmtree(os.path.join(LaunchOptions.minecraft_path, "resourcepacks", "PLauncher skins"))

            if LauncherConfig.IS_INTERNET and ely_by_var.get() and not default_skin_var.get():
                try:
                    uuid_response = requests.get(
                        fr"https://authserver.ely.by/api/users/profiles/minecraft/{username}",
                        timeout=5)
                    uuid_response.raise_for_status()
                    uuid = uuid_response.json()["id"]
                except Exception as e:
                    ToastNotification(master=root, title=language_manager.get("messages.titles.error"),
                                      message=language_manager.get("messages.texts.error.ely_by_uuid") + str(e),
                                      toast_type="error")
                    normal_state()
                    return
            else:
                if username not in LauncherConfig.config:
                    LauncherConfig.config[username] = str(uuid4())
                uuid = LauncherConfig.config[username]

            if LauncherConfig.version["profile"]:
                work_folder = os.path.join(LaunchOptions.minecraft_path, "profiles", "profile_" + LauncherConfig.version["profile"])
            else:
                work_folder = LaunchOptions.minecraft_path

            if LauncherConfig.config["custom_skin"] and not ely_by_var.get() and not default_skin_var.get():
                MinecraftTexturePackCreator(work_folder, LauncherConfig.config["custom_skin"]).run()

            save_config()
            args_custom = args_entry.get().split()

            callback = {
                "setMax": set_max_value,
                "setProgress": lambda val_prog: progress_bar_update(val_prog, progress_bar, status=False),
                "setStatus": set_status,
            }

            command, options = launch_service.build_command(
                selected_version=selected_version,
                work_folder=work_folder,
                username=username,
                uuid=uuid,
                memory_megabytes=LauncherConfig.config["memory_args"],
                custom_arguments=args_custom,
                java_choice=LauncherConfig.config["java"],
                check_java=check_var.get(),
                use_ely_by=LauncherConfig.IS_INTERNET and ely_by_var.get() and not default_skin_var.get(),
                callback=callback,
            )

            debug_mode = debug_var.get()

            process_service.run(
                command=command,
                working_directory=work_folder,
                debug=debug_mode,
                log_path="minecraft.log",
                on_log_opened=lambda log_file: setattr(LaunchOptions, "minecraft_log_file", log_file),
                on_started=lambda process, log_file: (
                    setattr(LaunchOptions, "minecraft_process", process),
                    setattr(LaunchOptions, "minecraft_log_file", log_file),
                ),
                on_running=lambda: (
                    root.withdraw() if hide_var.get() else None,
                    set_status(language_manager.get("main.status.loading_completed")),
                    launch_button.configure(
                        text=language_manager.get("main.buttons.complete_game"),
                        command=stop_action,
                        state="normal",
                    ),
                ),
                on_output=lambda line: print(line, end=""),
            )

            if hide_var.get():
                root.deiconify()

            if LaunchOptions.is_running and LaunchOptions.minecraft_process.returncode:
                raise Exception(language_manager.get("messages.texts.error.exit_code") + str(LaunchOptions.minecraft_process.returncode))

            normal_state()
            set_status(language_manager.get("main.status.game_completed"))
        except Exception as e:
            excepthook(*sys.exc_info())
            ToastNotification(master=root, 
                title=language_manager.get("messages.titles.error"),
                message=language_manager.get("messages.texts.error.launch") + str(e),
                toast_type="error"
            )
            normal_state()
            if hide_var.get():
                root.deiconify()
            set_status(language_manager.get("main.status.launch_error"))

            if LaunchOptions.is_running and LaunchOptions.minecraft_process and LaunchOptions.minecraft_process.returncode:
                LaunchOptions.minecraft_log_file.seek(0)
                crash_window.set_log_text(LaunchOptions.minecraft_log_file.read()[-50000:])
                root.after_idle(crash_window.open)
        finally:
            LaunchOptions.is_running = False
            if hasattr(LaunchOptions, 'minecraft_log_file') and LaunchOptions.minecraft_log_file:
                LaunchOptions.minecraft_log_file.close()

    def download_and_run():
        if LauncherConfig.IS_INTERNET:
            set_status(language_manager.get("main.status.loading"))
        try:
            if LauncherConfig.IS_INTERNET:
                if selected_version not in LauncherConfig.version["not_comp"]:
                    LauncherConfig.version["not_comp"].append(selected_version)
                    save_version()

                if selected_version not in LauncherConfig.version["download"]:
                    log("Загрузка файлов Minecraft...")
                    mcl.install.install_minecraft_version(selected_version, LaunchOptions.minecraft_path, callback={
                        "setMax": lambda val_max: set_max_value(val_max),
                        "setProgress": lambda val_prog: progress_bar_update(val_prog, progress_bar),
                        "setStatus": set_step,
                    })
                    log("Файлы Minecraft готовы.")

                elif check_var.get():
                    log("Проверка файлов Minecraft...")
                    mcl.install.install_minecraft_version(selected_version, LaunchOptions.minecraft_path)
                    log("Файлы Minecraft готовы.")

                if selected_version not in LauncherConfig.version["download"]:
                    LauncherConfig.version["download"].append(selected_version)
                    LauncherConfig.version["not_comp"].remove(selected_version)
                    root.after_idle(load_versions)

            LaunchOptions.is_running = True
            save_version()
            progress_bar.set(1)
            threading.Thread(target=run_minecraft).start()
        except Exception as e:
            excepthook(*sys.exc_info())
            save_version()
            normal_state()
            ToastNotification(master=root, title=language_manager.get("messages.titles.error"),
                              message=language_manager.get("messages.texts.error.loading") + str(e),
                              toast_type="error")
            set_status(language_manager.get("main.status.loading_error"))

    download_thread = threading.Thread(target=download_and_run)
    download_thread.start()

    def off_load():
        launch_button.configure(state="disabled", text=language_manager.get("main.status.finalizing"))
        kill_thread(download_thread)
        cancel()

    launch_button.configure(command=off_load, text=language_manager.get("main.buttons.cancel_loading"))
