def list_ver(loader):
    if not IS_INTERNET:
        return []
    other_versions_list = loaders_versions_mine[loader]
    choice_version_ctk.set(other_versions_list[0])

    return other_versions_list


def fun_install_loader():
    global loader_process
    progress_loader.configure(progress_color=dominant_color)
    try:
        val_call = {
            "setMax": set_max_value,
            "setProgress": lambda p: progress_bar_update(progress=p, bar=progress_loader, status=False)
        }
        version_select = choice_version_ctk.get()
        loader_select = choice_loader.get()
        if not get_java_path():
            mcl.runtime.install_jvm_runtime("jre-legacy", minecraft_path, callback=val_call)
        path_to_java = get_java_path()
        
        log(f"Downloading Minecraft version {version_select} with loader {loader_select}..", source="loaders")
        log(f"Java path: {path_to_java}", source="loaders")
        
        if loader_select == "Fabric":
            mcl.fabric.install_fabric(minecraft_version=version_select, minecraft_directory=minecraft_path,
                                      callback=val_call, java=path_to_java)
        elif loader_select == "Quilt":
            mcl.quilt.install_quilt(minecraft_version=version_select, minecraft_directory=minecraft_path,
                                    callback=val_call, java=path_to_java)
        elif loader_select == "Forge":
            mcl.forge.install_forge_version(mcl.forge.find_forge_version(version_select), path=minecraft_path,
                                            callback=val_call, java=path_to_java)
        elif loader_select == "OptiFine":
            mcl.install.install_minecraft_version(versionid=version_select,
                                                  minecraft_directory=minecraft_path, callback=val_call)
            get_ver = getVersion(mc_version=version_select)
            url = get_ver[version_select][0]["url"]
            response = requests.get(url)
            with open(os.path.join("ofb", 'Optifine.jar'), 'wb') as f:
                f.write(response.content)
            command = [
                path_to_java,
                '-jar',
                'Bridge.jar',
                minecraft_path
            ]
            loader_process = Popen(command, creationflags=CREATE_NO_WINDOW)
            loader_process.wait()
            loader_process = None
            os.remove(os.path.join("ofb", 'Optifine.jar'))
        elif loader_select == "NeoForge":
            mcl.install.install_minecraft_version(versionid=version_select,
                                                  minecraft_directory=minecraft_path, callback=val_call)
            mcl.neoforge.download_and_run(version=dictionary_neoforge[version_select], path_minecraft=minecraft_path,
                                          path_to_java=path_to_java)
        root.after(0, load_versions)
        log("Installation successful.", source="loaders")
        
    except Exception as e:
        excepthook(*sys.exc_info())
        new_message(title=language_manager.get("messages.titles.error"), message=language_manager.get("messages.texts.error.loading_loader") + str(e.__class__.__name__),
                    icon="warning", option_1=language_manager.get("messages.answers.ok"))


def fun_install_loaders():
    def off_load():
        install_loader.configure(state="disabled", text=language_manager.get("main.status.finalizing"))
        kill_thread(download_thread)
        if loader_process:
            loader_process.terminate()

    download_thread = threading.Thread(target=fun_install_loader)
    download_thread.start()
    install_loader.configure(command=off_load, text=language_manager.get("settings.4_page.cancel_loading"))
    launch_button.configure(state="disabled")
    
    download_thread.join()
    
    install_loader.configure(state="normal", text=language_manager.get("settings.4_page.install_loader"),
                             command=lambda: threading.Thread(target=fun_install_loaders).start())
    launch_button.configure(state="normal")
    progress_loader.configure(progress_color=lighten_dominant_5)


def get_loaders_versions():
    if not IS_INTERNET:
        return

    def load_forge():
        try:
            for version in mcl.forge.list_forge_versions():
                mc_version = version.split("-")[0]
                if mc_version not in forge_versions_mine:
                    forge_versions_mine.append(mc_version)
            forge_versions_mine.sort(key=Version, reverse=True)
        except Exception as e:
            log("Error fetching Forge versions:", "ERROR", source="loaders")
            excepthook(*sys.exc_info())

    def load_fabric():
        try:
            fabric = mcl.fabric.get_all_minecraft_versions()
            for v in fabric:
                fabric_versions_mine.append(v["version"])
        except Exception as e:
            log("Error fetching Fabric versions:", "ERROR", source="loaders")
            excepthook(*sys.exc_info())
    
    def load_quilt():
        try:
            quilt = mcl.quilt.get_all_minecraft_versions()
            for v in quilt:
                quilt_versions_mine.append(v["version"])
        except Exception as e:
            log("Error fetching Quilt versions:", "ERROR", source="loaders")
            excepthook(*sys.exc_info())
    
    def load_optifine():
        try:
            versions = getVersionList()
            optifine_version_mine.extend(versions)
        except Exception as e:
            log("Error fetching OptiFine versions:", "ERROR", source="loaders")
            excepthook(*sys.exc_info())
    
    def load_neoforge():
        global dictionary_neoforge
        try:
            dictionary_neoforge = mcl.neoforge.get_versions()
            neoforge_versions_mine.extend(dictionary_neoforge)
            neoforge_versions_mine.reverse()
        except Exception as e:
            log("Error fetching NeoForge versions:", "ERROR", source="loaders")
            excepthook(*sys.exc_info())
    
    threads = []
    for target in (load_forge, load_fabric, load_quilt, load_optifine, load_neoforge):
        t = threading.Thread(target=target)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    available_loaders = []
    if fabric_versions_mine:
        available_loaders.append("Fabric")
    if forge_versions_mine:
        available_loaders.append("Forge")
    if neoforge_versions_mine:
        available_loaders.append("NeoForge")
    if optifine_version_mine:
        available_loaders.append("OptiFine")
    if quilt_versions_mine:
        available_loaders.append("Quilt")

    root.after(0, lambda: choice_loader.configure(values=available_loaders))
    choice_loader.set(available_loaders[0] if available_loaders else "")

    if available_loaders:
        loader = choice_loader.get()
        versions_map = {
            "Fabric": fabric_versions_mine,
            "Forge": forge_versions_mine,
            "NeoForge": neoforge_versions_mine,
            "OptiFine": optifine_version_mine,
            "Quilt": quilt_versions_mine,
        }
        versions = versions_map.get(loader, [])

        choice_version.configure(values=versions)
        if versions:
            choice_version_ctk.set(versions[0])
            tab_buttons[tabs[3]].configure(state="normal")
        else:
            choice_version_ctk.set("")
    else:
        choice_version.configure(values=[])
        choice_version_ctk.set("")