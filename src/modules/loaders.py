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
        callbacks = {
            "setMax": set_max_value,
            "setProgress": lambda value: progress_bar_update(progress=value, bar=progress_loader, status=False),
        }
        selected_version = choice_version_ctk.get()
        selected_loader = choice_loader.get()
        if not selected_version or not selected_loader:
            return

        loader_installer.install(
            selected_loader,
            selected_version,
            callback=callbacks,
            neoforge_versions=LoadersVersions.dictionary_neoforge,
        )
        root.after_idle(load_versions)
        log("Установка успешно завершена")
    except Exception as error:
        log("Ошибка установки загрузчика:", level="ERROR")
        excepthook(*sys.exc_info())
        ToastNotification(
            title=language_manager.get("messages.titles.error"),
            message=language_manager.get("messages.texts.error.loading_loader") + str(error.__class__.__name__),
            toast_type="error",
        )

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

    catalog_targets = {
        "Forge": "forge_versions_mine",
        "Fabric": "fabric_versions_mine",
        "NeoForge": "neoforge_versions_mine",
        "OptiFine": "optifine_versions_mine",
        "Quilt": "quilt_versions_mine",
        "Cleanroom": "cleanroom_versions_mine",
    }

    def fetch_loader(name: str):
        try:
            versions, metadata = loader_catalog.fetch(name)
            target = getattr(LoadersVersions, catalog_targets[name])
            target.extend(versions)
            if name == "NeoForge":
                LoadersVersions.dictionary_neoforge = metadata
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
        except Exception as error:
            log(f"Ошибка получения версий для {name}: {error}", "WARNING")

    for loader_name in catalog_targets:
        threading.Thread(target=fetch_loader, args=(loader_name,), daemon=True).start()
