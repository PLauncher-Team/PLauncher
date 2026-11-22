from typing import Any

import customtkinter as ctk
from ratelimit import rate_limited

def configure(**dependencies: Any) -> None:
    globals().update(dependencies)


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
    version_store.save(LauncherConfig.version)


def save_config():
    config_store.save(LauncherConfig.config)


def set_version(e: str = None):
    if e:
        version_combobox_ctk.set(e)
        LauncherConfig.version["version"] = version_combobox_ctk.get() \
            .replace(language_manager.get("main.types_versions.not_completed"), "") \
            .replace(language_manager.get("main.types_versions.installed"), "")
        save_version()


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

        minecraft_directory = Path(LaunchOptions.minecraft_path)
        environment_service.directory = minecraft_directory
        profile_service.minecraft_directory = minecraft_directory
        profile_service.profiles_directory = minecraft_directory / "profiles"
        version_store.path = minecraft_directory / "version.json"
        java_runtime_service.minecraft_directory = minecraft_directory
        loader_installer.minecraft_directory = minecraft_directory
        launch_service.minecraft_directory = minecraft_directory
        LauncherConfig.version = version_store.load()
        environment_service.ensure()

        if not default_var.get():
            LauncherConfig.config["mine_path"] = LaunchOptions.minecraft_path
            save_config()

        root.after_idle(load_versions)
        list_profiles.configure(values=profile_controller.list_profiles())
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
        master=root,
        gui_options=GuiOptions,
        logger=log,
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




def center(work, x: int, y: int) -> str:
    POS_X = work.winfo_screenwidth() // 2 - x // 2
    POS_Y = work.winfo_screenheight() // 2 - y // 2
    CORD = f"{POS_X}+{POS_Y}"
    return CORD


def ex():
    new_message(
        master=root,
        gui_options=GuiOptions,
        logger=log,

        title=language_manager.get("messages.titles.warning"),
        message=language_manager.get("messages.texts.warning.exit"),
        icon="question",
        option_1=language_manager.get("messages.answers.no"),
        option_2=language_manager.get("messages.answers.yes")
    )
    if GuiOptions.msg.get() == language_manager.get("messages.answers.yes"):
        root.destroy()
        kernel32.ReleaseMutex(mutex)
        os._exit(0)
    else:
        GuiOptions.msg.grab_release()


def get_refresh_rate() -> int:
    monitors = win32api.EnumDisplayMonitors()
    max_refresh = 0

    monitor_info = win32api.GetMonitorInfo(monitors[0][0])
    device_name = monitor_info.get("Device")
    settings = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)
    current_refresh = getattr(settings, "DisplayFrequency", 0)

    if current_refresh > max_refresh:
        max_refresh = current_refresh

    return max_refresh if max_refresh != 0 else 60


def new_tooltip(**kwargs):
    CTkToolTip(
        **kwargs,
        x_offset=20,
        y_offset=10,
        bg_color=dominant_color,
        border_color=lighten_dominant_15
    )


class VersionFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(
            master,
            fg_color="#111111",
            corner_radius=20,
            border_width=2,
            border_color="#FFFFFF"
        )
        pywinstyles.set_opacity(self, value=0.6, color="#242424")
        self.url = "https://github.com/PLauncher-Team/PLauncher/releases/latest"
        self.version_label = ctk.CTkLabel(
            self,
            text=LauncherConfig.CURRENT_VERSION,
            font=("Segoe UI", 24, "bold"),
            text_color="white"
        )
        self.version_label.place(relx=0.5, rely=0.5, anchor="center")
        self.new_label = None
        threading.Thread(target=self._update_check, daemon=True).start()

    def is_newer_version(self, latest_tag: str, current_tag: str) -> bool:
        try:
            return packaging.version.Version(latest_tag.lstrip('v')) > packaging.version.Version(current_tag.lstrip('v'))
        except Exception:
            return False

    def check_update(self, current_version: str) -> str | bool:
        if not LauncherConfig.IS_INTERNET:
            return False
        try:
            latest_tag = mcl.utils.get_github_tags("PLauncher-Team", "PLauncher")[0]
            if latest_tag and self.is_newer_version(latest_tag, current_version):
                log(f"Доступно обновление: {current_version} -> {latest_tag}")
                return latest_tag
            else:
                return False
        except Exception as e:
            log(f"Ошибка получения информации о новой версии: {e}", "ERROR")
            return False

    def open_download(self, event: object = None):
        webbrowser.open(self.url)

    def _update_check(self):
        new_tag = self.check_update(LauncherConfig.CURRENT_VERSION)
        if new_tag:
            self.after(0, lambda: self._display_new_version(new_tag))

    def _display_new_version(self, new_tag: str):
        self.version_label.configure(text=new_tag)
        self.version_label.place_configure(rely=0.2, anchor="n")
        self.new_label = ctk.CTkLabel(
            self,
            text="new version",
            font=("Segoe UI", 14, "bold"),
            text_color="#FFD700"
        )
        self.new_label.place(relx=0.5, rely=0.8, anchor="s")
        self._bind_click_area()

    def _bind_click_area(self):
        self._set_bind(self)
        for child in self.winfo_children():
            self._set_bind(child)

    def _set_bind(self, widget):
        widget.bind("<Button-1>", self.open_download)
        widget.configure(cursor="hand2")
        widget.bind("<Enter>", lambda e: self.configure(fg_color="#111111"))
        widget.bind("<Leave>", lambda e: self.configure(fg_color="#000001"))


def apply_hover_border():
    widget_list = [launch_button, version_combobox_ctk, username_entry, settings_button, mods_button, logs_button,
                   feedback_button, version_combobox.search_entry,
                   mod_viewer_window.search_entry, mod_viewer_window.refresh_btn, mod_viewer_window.lock_all_btn,
                   mod_viewer_window.unlock_all_btn, mod_viewer_window.close_btn, installed_versions_combobox_ctk, del_version, java_combobox,
                   memory_combobox, args_entry, open_folder, change_folder, update_skin_button, select_skin_button, choice_version_ctk, choice_loader,
                   install_loader, list_profiles, add_profile_Entry, add_profile_button, del_profile_button, rename_profile_button,
                   open_profile, del_java_button, back_btn, crash_window.ai_button]
    original_borders = {}

    for widget in widget_list:
        original_borders[widget] = widget.cget("border_width")
        widget.configure(border_width=0)
        widget.bind("<Enter>", lambda e, w=widget, orig=original_borders[widget]:
        w.configure(border_width=orig) if w.cget("state") != "disabled" else None)
        widget.bind("<Leave>", lambda e, w=widget: w.configure(border_width=0))


import os


def restart_app_with_bat():
    script_path = os.path.abspath(sys.argv[0])
    _, ext = os.path.splitext(script_path.lower())

    if ext == ".exe":
        launcher = f'start "" "{script_path}"'
    else:
        launcher = f'start "" "pythonw" "{script_path}"'

    bat = f"""@echo off
timeout /t 1 > nul
{launcher}
del "%~f0"
"""
    bat_path = os.path.join(os.getcwd(), "restart.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat)

    subprocess.Popen(bat_path, creationflags=subprocess.CREATE_NO_WINDOW)

    kernel32.ReleaseMutex(mutex)
    os._exit(0)


def select_language(selected_value: str):
    texts_language_reverse = {value: key for key, value in language_manager.get_languages_names().items()}
    if LauncherConfig.config["language"] == selected_value:
        return

    new_lang = texts_language_reverse[selected_value]
    LauncherConfig.config["language"] = new_lang
    save_config()

    new_message(
        master=root,
        gui_options=GuiOptions,
        logger=log,
title=language_manager.get("messages.titles.warning"),
        message=language_manager.get("messages.texts.warning.language"),
        icon="question",
        option_1=language_manager.get("messages.answers.no"),
        option_2=language_manager.get("messages.answers.yes")
    )

    if GuiOptions.msg.get() == language_manager.get("messages.answers.yes"):
        log("Перезапуск приложения для смены языка")
        root.destroy()
        kernel32.ReleaseMutex(mutex)
        restart_app_with_bat()



