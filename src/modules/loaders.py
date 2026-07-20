from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


def list_ver(loader: str) -> list:
    if not LauncherConfig.IS_INTERNET:
        return []
    other_versions_list = LoadersVersions.loaders_versions_mine[loader]
    choice_version_ctk.set(other_versions_list[0])
    return other_versions_list


def fun_install_loader():
    try:
        val_call = {
            "setMax": set_max_value,
            "setProgress": lambda p: progress_bar_update(progress=p, bar=progress_loader, status=False)
        }
        version_select = choice_version_ctk.get()
        loader_select = choice_loader.get()

        if not version_select or not loader_select:
            return

        java_major = LaunchOptions.available_major_versions[-1]

        if not JavaRuntimeManager.get_any_java_exe(java_major):
            log(f"Установка JVM {java_major} runtime")
            JavaRuntimeManager.download_and_extract_java(java_major, callback=val_call)
        path_to_java = JavaRuntimeManager.get_any_java_exe(java_major)

        log(f"Загрузка версии Minecraft {version_select} с загрузчиком {loader_select}..")
        log(f"Путь к Java: {path_to_java}")

        if loader_select == "Fabric":
            mcl.fabric.install_fabric(minecraft_version=version_select, minecraft_directory=LaunchOptions.minecraft_path,
                                      callback=val_call, java=path_to_java)
        elif loader_select == "Quilt":
            mcl.quilt.install_quilt(minecraft_version=version_select, minecraft_directory=LaunchOptions.minecraft_path,
                                    callback=val_call, java=path_to_java)
        elif loader_select == "Forge":
            mcl.forge.install_forge_version(mcl.forge.find_forge_version(version_select), path=LaunchOptions.minecraft_path,
                                            callback=val_call, java=path_to_java)
        elif loader_select == "OptiFine":
            mcl.install.install_minecraft_version(versionid=version_select,
                                                  minecraft_directory=LaunchOptions.minecraft_path, callback=val_call)
            get_ver = optipy.getVersion(mc_version=version_select)
            url = get_ver[version_select][0]["url"]
            response = requests.get(url)
            with open(os.path.join("ofb", 'Optifine.jar'), 'wb') as f:
                f.write(response.content)
            command_str = f'"{path_to_java}" -jar Bridge.jar "{LaunchOptions.minecraft_path}" -log=console > optifine.log 2>&1'

            LaunchOptions.loader_process = subprocess.Popen(
                command_str,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            LaunchOptions.loader_process.wait()
            LaunchOptions.loader_process = None
            os.remove(os.path.join("ofb", 'Optifine.jar'))
        elif loader_select == "NeoForge":
            mcl.install.install_minecraft_version(versionid=version_select,
                                                  minecraft_directory=LaunchOptions.minecraft_path, callback=val_call)
            mcl.neoforge.download_and_run(version=LoadersVersions.dictionary_neoforge[version_select], path_minecraft=LaunchOptions.minecraft_path,
                                          java=path_to_java)
        
        elif loader_select == "Cleanroom":
            mcl.install.install_minecraft_version(versionid="1.12.2",
                                                  minecraft_directory=LaunchOptions.minecraft_path, callback=val_call)
            mcl.cleanroom.download_and_run(version=version_select, path_minecraft=LaunchOptions.minecraft_path, java=path_to_java)
            
            
        root.after_idle(load_versions)
        log(f"Установка успешно завершена")

    except Exception as e:
        log(f"Ошибка установки загрузчика:", level="ERROR")
        excepthook(*sys.exc_info())
        ToastNotification(title=language_manager.get("messages.titles.error"),
                          message=language_manager.get("messages.texts.error.loading_loader") + str(e.__class__.__name__),
                          toast_type="error")


def fun_install_loaders():
    def off_load():
        install_loader.configure(state="disabled", text=language_manager.get("main.status.finalizing"))
        kill_thread(download_thread)
        if LaunchOptions.loader_process:
            LaunchOptions.loader_process.terminate()

    download_thread = threading.Thread(target=fun_install_loader)
    download_thread.start()
    install_loader.configure(command=off_load, text=language_manager.get("settings.4_page.cancel_loading"))
    launch_button.configure(state="disabled")

    download_thread.join()

    progress_loader.set(0)
    install_loader.configure(state="normal", text=language_manager.get("settings.4_page.install_loader"),
                             command=lambda: threading.Thread(target=fun_install_loaders).start())
    launch_button.configure(state="normal")


def get_loaders_versions():
    if not LauncherConfig.IS_INTERNET:
        return

    def get_neoforge():
        LoadersVersions.dictionary_neoforge = mcl.neoforge.get_versions()
        LoadersVersions.neoforge_versions_mine.extend(
            sorted(LoadersVersions.dictionary_neoforge.keys(), reverse=True)
        )

    def fetch_loader(name, fetch_func, version_list_attr):
        try:
            fetch_func()
            versions = getattr(LoadersVersions, version_list_attr)
            log(f"Загружено версий для {name}: {len(versions)}.", "INFO")

            def update_ui():
                available_loaders = list(choice_loader.cget("values"))
                if name not in available_loaders:
                    available_loaders.append(name)
                    choice_loader.configure(values=available_loaders)
                    if not choice_loader.get():
                        choice_loader.set(name)

                if choice_loader.get() == name:
                    choice_version.configure(values=versions)
                    if versions:
                        choice_version_ctk.set(versions[0])
            content_frames[tabs[3]].after_idle(update_ui)
        except Exception as e:
            log(f"Ошибка получения версий для {name}: {e}", "WARNING")

    loaders = [
        (
            "Forge",
            lambda: LoadersVersions.forge_versions_mine.extend(
                sorted(
                    dict.fromkeys(
                        v.split("-")[0]
                        for v in mcl.forge.list_forge_versions()
                        if packaging.version.Version(v.split("-")[0]) >= packaging.version.Version("1.7.10")
                    ),
                    key=packaging.version.Version,
                    reverse=True
                )
            ),
            "forge_versions_mine"
        ),
        ("Fabric", lambda: [LoadersVersions.fabric_versions_mine.append(v["version"])
                            for v in mcl.fabric.get_all_minecraft_versions()], "fabric_versions_mine"),
        ("NeoForge", get_neoforge, "neoforge_versions_mine"),
        ("OptiFine", lambda: LoadersVersions.optifine_versions_mine.extend(optipy.getVersionList()), "optifine_versions_mine"),
        ("Quilt", lambda: LoadersVersions.quilt_versions_mine.extend(
            [v["version"] for v in mcl.quilt.get_all_minecraft_versions()]), "quilt_versions_mine"),
        ("Cleanroom", lambda: LoadersVersions.cleanroom_versions_mine.extend(mcl.cleanroom.get_github_tags("CleanroomMC", "Cleanroom")), "cleanroom_versions_mine")
    ]

    for name, func, attr in loaders:
        threading.Thread(target=fetch_loader, args=(name, func, attr), daemon=True).start()
