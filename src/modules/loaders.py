from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *

def list_ver(loader: str) -> list:
    """Returns a list of available versions for the specified loader.
    If no internet connection, returns empty list."""
    if not LauncherConfig.IS_INTERNET:
        return []
    other_versions_list = LoadersVersions.loaders_versions_mine[loader]
    choice_version_ctk.set(other_versions_list[0])
    return other_versions_list


def fun_install_loader():
    """Main function for installing Minecraft loaders (Fabric, Quilt, Forge, etc.)"""
    try:
        val_call = {
            "setMax": set_max_value,
            "setProgress": lambda p: progress_bar_update(progress=p, bar=progress_loader, status=False)
        }
        version_select = choice_version_ctk.get()
        loader_select = choice_loader.get()
        
        if not version_select or not loader_select:
            return
        # Install Java if not installed
        if not get_java_path():
            log("Installing JVM runtime", source="loaders")
            mcl.runtime.install_jvm_runtime("jre-legacy", LaunchOptions.minecraft_path, callback=val_call)
        path_to_java = get_java_path()

        log(f"Downloading Minecraft version {version_select} with loader {loader_select}..", source="loaders")
        log(f"Java path: {path_to_java}", source="loaders")

        # Handle different loader types
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
            # Special handling for OptiFine installation
            mcl.install.install_minecraft_version(versionid=version_select,
                                                  minecraft_directory=LaunchOptions.minecraft_path, callback=val_call)
            get_ver = optipy.getVersion(mc_version=version_select)
            url = get_ver[version_select][0]["url"]
            response = requests.get(url)
            with open(os.path.join("ofb", 'Optifine.jar'), 'wb') as f:
                f.write(response.content)
            command = [
                path_to_java,
                '-jar',
                'Bridge.jar',
                LaunchOptions.minecraft_path
            ]
            LaunchOptions.loader_process = subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
            LaunchOptions.loader_process.wait()
            LaunchOptions.loader_process = None
            os.remove(os.path.join("ofb", 'Optifine.jar'))
        elif loader_select == "NeoForge":
            mcl.install.install_minecraft_version(versionid=version_select,
                                                  minecraft_directory=LaunchOptions.minecraft_path, callback=val_call)
            mcl.neoforge.download_and_run(version=LoadersVersions.dictionary_neoforge[version_select], path_minecraft=LaunchOptions.minecraft_path,
                                          java=path_to_java)

        # Refresh versions list after installation
        root.after(0, load_versions)
        log(f"Installation successful", source="loaders")

    except Exception as e:
        log(f"Loader installation failed:", level="ERROR", source="loaders")
        excepthook(*sys.exc_info())
        ToastNotification(title=language_manager.get("messages.titles.error"),
                    message=language_manager.get("messages.texts.error.loading_loader") + str(e.__class__.__name__),
                    toast_type="error")


def fun_install_loaders():
    """Wrapper function for loader installation that handles threading and UI updates"""
    def off_load():
        """Callback function to cancel the installation process"""
        install_loader.configure(state="disabled", text=language_manager.get("main.status.finalizing"))
        kill_thread(download_thread)
        if LaunchOptions.loader_process:
            LaunchOptions.loader_process.terminate()

    # Start installation in a separate thread
    download_thread = threading.Thread(target=fun_install_loader)
    download_thread.start()
    install_loader.configure(command=off_load, text=language_manager.get("settings.4_page.cancel_loading"))
    launch_button.configure(state="disabled")

    download_thread.join()

    # Restore UI after installation completes
    install_loader.configure(state="normal", text=language_manager.get("settings.4_page.install_loader"),
                             command=lambda: threading.Thread(target=fun_install_loaders).start())
    launch_button.configure(state="normal")
    progress_loader.set(0)


def get_loaders_versions():
    """Fetches available versions for all loaders (Forge, Fabric, etc.) in parallel threads"""
    if not LauncherConfig.IS_INTERNET:
        return

    def load_forge():
        """Load available Forge versions"""
        try:
            for version in mcl.forge.list_forge_versions():
                mc_version = version.split("-")[0]
                if mc_version not in LoadersVersions.forge_versions_mine:
                    LoadersVersions.forge_versions_mine.append(mc_version)
            LoadersVersions.forge_versions_mine.sort(key=packaging.version.Version, reverse=True)
        except Exception as e:
            log(f"Error fetching Forge versions:", "ERROR", "loaders")
            excepthook(*sys.exc_info())

    def load_fabric():
        """Load available Fabric versions"""
        try:
            for v in mcl.fabric.get_all_minecraft_versions():
                LoadersVersions.fabric_versions_mine.append(v["version"])
        except Exception as e:
            log(f"Error fetching Fabric versions:", "ERROR", "loaders")
            excepthook(*sys.exc_info())

    def load_quilt():
        """Load available Quilt versions"""
        try:
            for v in mcl.quilt.get_all_minecraft_versions():
                LoadersVersions.quilt_versions_mine.append(v["version"])
        except Exception as e:
            log(f"Error fetching Quilt versions:", "ERROR", "loaders")
            excepthook(*sys.exc_info())

    def load_optifine():
        """Load available OptiFine versions"""
        try:
            LoadersVersions.optifine_version_mine.extend(optipy.getVersionList())
        except Exception as e:
            log(f"Error fetching OptiFine versions:", "ERROR", "loaders")
            excepthook(*sys.exc_info())

    def load_neoforge():
        """Load available NeoForge versions"""
        try:
            LoadersVersions.dictionary_neoforge = mcl.neoforge.get_versions()
            LoadersVersions.neoforge_versions_mine.extend(LoadersVersions.dictionary_neoforge)
            LoadersVersions.neoforge_versions_mine.reverse()
        except Exception as e:
            log(f"Error fetching NeoForge versions:", "ERROR", "loaders")
            excepthook(*sys.exc_info())

    # Start all loader version fetchers in parallel threads
    threads = []
    for target in (load_forge, load_fabric, load_optifine, load_quilt, load_neoforge):
        t = threading.Thread(target=target)
        t.start()
        threads.append(t)

    # Wait for all threads to complete
    for t in threads:
        t.join()

    # Update UI with available loaders
    available_loaders = []
    if LoadersVersions.fabric_versions_mine:
        available_loaders.append("Fabric")
    if LoadersVersions.forge_versions_mine:
        available_loaders.append("Forge")
    if LoadersVersions.neoforge_versions_mine:
        available_loaders.append("NeoForge")
    if LoadersVersions.optifine_version_mine:
        available_loaders.append("OptiFine")
    if LoadersVersions.quilt_versions_mine:
        available_loaders.append("Quilt")
    
    if len(available_loaders) == 5:
        log("Loaders list successfully loaded", source="loaders")
    
    choice_loader.configure(values=available_loaders)
    choice_loader.set(available_loaders[0] if available_loaders else "")

    # Update versions list for the selected loader
    if available_loaders:
        loader = choice_loader.get()
        versions_map = {
            "Fabric": LoadersVersions.fabric_versions_mine,
            "Forge": LoadersVersions.forge_versions_mine,
            "NeoForge": LoadersVersions.neoforge_versions_mine,
            "OptiFine": LoadersVersions.optifine_version_mine,
            "Quilt": LoadersVersions.quilt_versions_mine,
        }
        versions = versions_map.get(loader, [])

        choice_version.configure(values=versions)
        if versions:
            choice_version_ctk.set(versions[0])
            tab_switch._buttons_dict[tabs[3]].configure(state="normal")
        else:
            choice_version_ctk.set("")
    else:
        choice_version.configure(values=[])
        choice_version_ctk.set("")