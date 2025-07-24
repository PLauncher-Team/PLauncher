import os.path


def thread_load_versions():
    global versions
    if IS_INTERNET:
        versions = mcl.utils.get_version_list()
        log(f"Version list retrieved: {len(versions)} items", source="launcher_core")
    root.after(0, load_versions)


def save_versions_var():
    config["release"]    = release_var.get()
    config["snapshot"]   = snapshot_var.get()
    config["old_beta"]   = old_beta_var.get()
    config["old_alpha"]  = old_alpha_var.get()
    save_config(config)


def load_versions():
    global latest_version, IS_INTERNET, version, old_types_versions
    if version["version"]:
        latest_version = version["version"]
    try:
        installed_versions = mcl.utils.get_installed_versions(minecraft_path)

        installed_versions_ids = {version['id'] for version in installed_versions}

        show_release = release_var.get()
        show_snapshot = snapshot_var.get()
        show_old_beta = old_beta_var.get()
        show_old_alpha = old_alpha_var.get()
        
        old_types_versions = [show_release, show_snapshot, show_old_beta, show_old_alpha]
        
        filtered_versions = [
            version for version in versions
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
        installed_versions_combobox_ctk.set(installed_versions_list[0] if installed_versions_list else "")

        for i, value_dow in enumerate(installed_versions_list):
            if value_dow in version["download"]:
                installed_versions_list[i] += language_manager.get("main.types_versions.installed")
            elif value_dow in version["not_comp"]:
                installed_versions_list[i] += language_manager.get("main.types_versions.not_completed")

        version_combobox.configure(values=installed_versions_list + other_versions_list)
    except Exception as e:
        excepthook(*sys.exc_info())
        new_message(title=language_manager.get("messages.titles.error"), message=language_manager.get("messages.texts.error.loading") + str(e), icon="cancel",
                    option_1=language_manager.get("messages.answers.ok"))
    
    if latest_version in version["download"]:
        check_version = latest_version + language_manager.get("main.types_versions.installed")
    elif latest_version in version["not_comp"]:
        check_version = latest_version + language_manager.get("main.types_versions.not_completed")
    else:
        check_version = latest_version
    if check_version not in version_combobox.values:
        version_combobox_ctk.set("")
    else:
        if latest_version in version["download"]:
            version_combobox_ctk.set(latest_version + language_manager.get("main.types_versions.installed"))
        elif latest_version in version["not_comp"]:
            version_combobox_ctk.set(latest_version + language_manager.get("main.types_versions.not_completed"))
        else:
            version_combobox_ctk.set(latest_version)
    
    log("Version list successfully loaded", source="launcher_core")


def stop_action():
    global minecraft_process, is_running, minecraft_log_file
    launch_button.configure(text=language_manager.get("main.status.finalizing"), state="disabled")
    if is_running:
        minecraft_log_file.close()
        is_running = False
        try:
            log("Terminating Minecraft process.", source="launcher_core")
            minecraft_process.terminate()
            minecraft_process.wait(timeout=5)
            log("Minecraft process terminated gracefully.", source="launcher_core")
        except subprocess.TimeoutExpired:
            log("Timeout expired; killing Minecraft process.", source="launcher_core")
            minecraft_process.kill()
            log("Minecraft process killed.", source="launcher_core")


def set_step(value):
    global step
    step = language_manager.get("main.mcl_status." + value)


def set_max_value(max_value):
    global total_files
    total_files = max_value


def fun_progres(progress, bar):
    bar.set(progress / total_files)


@rate_limited(period=0.1, calls=5, raise_on_limit=False)
def progress_bar_update(progress=None, bar=None, check=True, status=True):
    if check:
        if status:
            set_status(f"{step} ({progress}/{total_files})")
        fun_progres(progress, bar)


def set_status(status):
    status_label.configure(text=status)
    

@rate_limited(period=1, calls=2, raise_on_limit=False)
def launch_game():
    global minecraft_process, is_running, IS_INTERNET, version, config
    crash_window.withdraw()
    selected_version = version_combobox_ctk.get().replace(language_manager.get("main.types_versions.not_completed"), "").replace(language_manager.get("main.types_versions.installed"), "")
    username = config["name"]
    if not selected_version:
        new_message(title=language_manager.get("messages.titles.warning"), message=language_manager.get("messages.texts.warning.version"),
                    icon="warning", option_1=language_manager.get("messages.answers.ok"))
        return
    if not config["memory_args"]:
        config["memory_args"] = default_config["memory_args"]
        selected_memory.set(value=default_config["memory_args"])

    progress_bar.configure(progress_color=dominant_color)
    progress_bar.set(0)
    for obj in settings_button, logs_button, feedback_button:
        obj.configure(state="disabled")

    def cancel():
        set_status(language_manager.get("main.status.loading_canceled"))
        save_version(version)
        normal_state()
    
    def normal_state():
        launch_button.configure(text=language_manager.get("main.buttons.launch_game"), command=lambda: threading.Thread(target=launch_game).start(), state="normal")
        progress_bar.configure(progress_color=lighten_dominant_5)
        for obj in settings_button, logs_button, feedback_button:
            obj.configure(state="normal")


    def run_minecraft():
        global minecraft_process, is_running, version, minecraft_log_file
        try:
            if os.path.isdir(os.path.join(minecraft_path, "resourcepacks", "PLauncher skins")):
                shutil.rmtree(os.path.join(minecraft_path, "resourcepacks", "PLauncher skins"))
            if IS_INTERNET and ely_by_var.get() and not default_skin_var.get():
                try:
                    uuid_response = requests.get(fr"https://authserver.ely.by/api/users/profiles/minecraft/{username}",
                                                 timeout=5)
                    uuid_response.raise_for_status()
                    uuid = uuid_response.json()["id"]
                except Exception as e:
                    excepthook(*sys.exc_info())
                    new_message(title=language_manager.get("messages.titles.error"), message=language_manager.get("messages.texts.error.ely_by_uuid") + str(e), icon="cancel",
                                option_1=language_manager.get("messages.answers.ok"))
                    normal_state()
                    return
            else:
                if username not in config:
                    config[username] = str(uuid4())
                uuid = config[username]
            if config["custom_skin"] and not ely_by_var.get() and not default_skin_var.get():
                MinecraftTexturePackCreator(minecraft_path, config["custom_skin"]).run()

            if version["profile"]:
                work_folder = os.path.join(minecraft_path, "profiles", "profile_" + version["profile"])
            else:
                work_folder = minecraft_path
            
            save_config(config)
            args_custom = args_entry.get().split()
            
            options = {
                "gameDirectory": work_folder,
                "username": username,
                "uuid": uuid,
                "jvmArguments": args_custom + ["-Xmx" + config["memory_args"] + "M",
                                               "-Xms" + str(int(config["memory_args"]) // 2) + "M",
                                               "-Djavax.net.ssl.trustStoreType=Windows-ROOT"]
            }
            
            if config["java"]:
                options["executablePath"] = config["java_paths"][config["java"]]
            
            if IS_INTERNET and ely_by_var.get() and not default_skin_var.get():
                options["jvmArguments"].append(rf"-javaagent:{os.path.abspath('injector.jar')}=ely.by")

            command = mcl.command.get_minecraft_command(selected_version, minecraft_path, options)
            debug_mode = debug_var.get()

            creationflags = 0
            if not debug_mode:
                creationflags = subprocess.CREATE_NO_WINDOW

            minecraft_log_file = open("minecraft.log", "w+", encoding="cp1251", errors="replace")

            
            log("Launching Minecraft\n"
                f"Version: {selected_version}\n"
                f"User: {username}\n"
                f"Args: {", ".join(options['jvmArguments'])}\n"
                f"Java: {command[0]}\n"
                f"Working directory: {work_folder}\n"
                f"Debug: {debug_mode}\n"
                f"UUID: {uuid}",
                source="launcher_core")

            hJob = win32job.CreateJobObject(None, "PLauncher_Job")
            extended_info = win32job.QueryInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation)
            extended_info["BasicLimitInformation"]["LimitFlags"] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            win32job.SetInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation, extended_info)
            
            minecraft_process = subprocess.Popen(
                command,
                cwd=work_folder,
                creationflags=creationflags,
                stdout=minecraft_log_file,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            win32job.AssignProcessToJobObject(hJob, int(minecraft_process._handle))
        
            if hide_var.get():
                root.withdraw()
            set_status(language_manager.get("main.status.loading_completed"))
            launch_button.configure(text=language_manager.get("main.buttons.complete_game"), command=stop_action, state="normal")
        
            minecraft_process.wait()
            
            if hide_var.get():
                root.deiconify()
        
            if is_running and minecraft_process.returncode:
                raise Exception(language_manager.get("messages.texts.error.exit_code") + str(minecraft_process.returncode))
        
            normal_state()
            set_status(language_manager.get("main.status.game_completed"))
            is_running = False
            minecraft_log_file.close()
        except Exception as e:
            excepthook(*sys.exc_info())
            new_message(
                title=language_manager.get("messages.titles.error"),
                message=language_manager.get("messages.texts.error.launch") + str(e),
                icon="cancel",
                option_1=language_manager.get("messages.answers.ok"),
            )
            normal_state()
            if hide_var.get():
                root.deiconify()
            set_status(language_manager.get("main.status.launch_error"))
            if is_running and minecraft_process.returncode:
                minecraft_log_file.seek(0)
                crash_window.set_log_text(minecraft_log_file.read()[-50000:])
                root.after(0, crash_window.open)
            is_running = False
            if "log_file" in locals():
                minecraft_log_file.close()

    def download_and_run():
        global is_running, IS_INTERNET, version
        if IS_INTERNET:
            set_status(language_manager.get("main.status.loading"))
        try:
            if IS_INTERNET:
                if selected_version not in version["not_comp"]:
                    version["not_comp"].append(selected_version)
                    save_version(version)
                    root.after(0, load_versions)

                if selected_version not in version["download"]:
                    log("Downloading Minecraft files...", source="launcher_core")
                    mcl.install.install_minecraft_version(selected_version, minecraft_path, callback={
                        "setMax": lambda val_max: set_max_value(val_max),
                        "setProgress": lambda val_prog: progress_bar_update(val_prog, progress_bar),
                        "setStatus": set_step,
                    })
                    log("Minecraft files are ready.", source="launcher_core")
                    
                elif check_var.get():
                    log("Verifying Minecraft files...", source="launcher_core")
                    mcl.install.install_minecraft_version(selected_version, minecraft_path, callback={
                        "setProgress": lambda val_prog: progress_bar_update(check=False)
                    })
                    log("Minecraft files are ready.", source="launcher_core")
                    
                if selected_version not in version["download"]:
                    version["download"].append(selected_version)
                    version["not_comp"].remove(selected_version)
                    root.after(0, load_versions)
            
            is_running = True
            save_version(version)
            progress_bar.set(1)
            threading.Thread(target=run_minecraft).start()
        except Exception as e:
            excepthook(*sys.exc_info())
            save_version(version)
            normal_state()
            new_message(title=language_manager.get("messages.titles.error"), message=language_manager.get("messages.texts.error.loading") + str(e), icon="cancel",
                        option_1=language_manager.get("messages.answers.ok"))
            set_status(language_manager.get("main.status.loading_error"))
    
    
    download_thread = threading.Thread(target=download_and_run)
    download_thread.start()

    def off_load():
        launch_button.configure(state="disabled", text=language_manager.get("main.status.finalizing"))
        kill_thread(download_thread)
        cancel()

    launch_button.configure(command=off_load, text=language_manager.get("main.status.loading"))
