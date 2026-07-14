from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


def profile_select(*args):
    current = list_profiles.get()
    LauncherConfig.version["profile"] = False if current == language_manager.get("settings.4_page.no") else current
    save_version()
    mod_viewer_window._first_load_done = False
    log(f"Выбран профиль: {current}")


def del_profile():
    current = list_profiles.get()
    if current != language_manager.get("settings.4_page.no"):
        new_message(
            title=language_manager.get("messages.titles.warning"),
            message=f"{language_manager.get('messages.texts.warning.profile')} ({current})",
            icon="question",
            option_1=language_manager.get("messages.answers.no"),
            option_2=language_manager.get("messages.answers.yes")
        )
        if GuiOptions.msg.get() == language_manager.get("messages.answers.yes"):
            log(f"Удаление профиля: {current}")
            if os.path.isdir(os.path.join(LaunchOptions.minecraft_path, "profiles", "profile_" + current)):
                shutil.rmtree(os.path.join(LaunchOptions.minecraft_path, "profiles", "profile_" + current))

            list_profiles.configure(values=list_dir())
            first = list_profiles.cget("values")[0] if list_profiles.cget("values")[0] != "" else language_manager.get("settings.4_page.no")
            list_profiles.set(first)
            LauncherConfig.version["profile"] = False if first == language_manager.get("settings.4_page.no") else first
            save_version()
            log(f"Профиль {current} успешно удалён")


def _add_profile():
    rename_profile_button.configure(state="normal")
    list_profiles.configure(state="readonly")
    open_profile.configure(state="normal")
    add_profile_Entry.delete(0, ctk.END)
    add_profile_Entry.lower()
    del_profile_button.configure(
        text=language_manager.get("settings.4_page.delete"),
        command=del_profile
    )
    add_profile_button.configure(
        text=language_manager.get("settings.4_page.add"),
        command=fun_add_profile
    )


def save_add_profile():
    name = add_profile_Entry.get().strip()
    no = language_manager.get("settings.4_page.no")
    if not name or name == no:
        return

    log(f"Создание нового профиля: {name}")
    try:
        profile_path = os.path.join(LaunchOptions.minecraft_path, "profiles", "profile_" + name)
        os.makedirs(profile_path)

        dirs = ["assets", "bin", "libraries", "logs", "resourcepacks", "saves",
                "screenshots", "shaderpacks", "versions", "profiles", "mods"]

        for directory in dirs:
            os.makedirs(os.path.join(profile_path, directory), exist_ok=True)
        log(f"Профиль {name} успешно создан с {len(dirs)} директориями")
    except Exception as e:
        log(f"Не удалось создать профиль {name}: {e}", level="ERROR")
        excepthook(*sys.exc_info())
        ToastNotification(
            title=language_manager.get("messages.titles.error"),
            message=language_manager.get("messages.texts.error.profile_add") + str(e),
            toast_type="error",
        )
    else:
        if list_profiles.cget("values") == (no,):
            LauncherConfig.version["profile"] = name
            list_profiles.set(name)
            save_version()
        list_profiles.configure(state="readonly")
        save_version()
        list_profiles.configure(values=list_dir())
        add_profile_Entry.delete(0, ctk.END)
        add_profile_Entry.lower()
        del_profile_button.configure(
            text=language_manager.get("settings.4_page.delete"),
            command=del_profile
        )
        add_profile_button.configure(
            text=language_manager.get("settings.4_page.add"),
            command=fun_add_profile
        )
        open_profile.configure(state="normal")
        rename_profile_button.configure(state="normal")


def fun_add_profile():
    add_profile_Entry.lift()
    rename_profile_button.configure(state="disabled")
    list_profiles.configure(state="disabled")
    open_profile.configure(state="disabled")
    del_profile_button.configure(
        text=language_manager.get("messages.answers.no"),
        command=_add_profile
    )
    add_profile_button.configure(
        text=language_manager.get("settings.4_page.save"),
        command=save_add_profile
    )


def list_dir() -> list:
    profiles_dir = os.path.join(LaunchOptions.minecraft_path, "profiles")
    return [language_manager.get("settings.4_page.no")] + [
        g[8:] for g in os.listdir(profiles_dir) if len(g) >= 9 and os.path.isdir(os.path.join(profiles_dir, g))
    ]


def rename_profile(old_name: str):
    new_name = add_profile_Entry.get().strip()
    no = language_manager.get("settings.4_page.no")
    if not new_name or new_name == old_name or new_name == no:
        return

    try:
        os.rename(
            os.path.join(LaunchOptions.minecraft_path, "profiles", "profile_" + old_name),
            os.path.join(LaunchOptions.minecraft_path, "profiles", "profile_" + new_name)
        )
        log(f"Профиль успешно переименован")
    except Exception as e:
        log(f"Не удалось переименовать профиль:", level="ERROR")
        excepthook(*sys.exc_info())
        ToastNotification(
            title=language_manager.get("messages.titles.error"),
            message=language_manager.get("messages.texts.error.profile_rename") + str(e),
            toast_type="cancel"
        )
    else:
        if LauncherConfig.version["profile"] == old_name:
            list_profiles.set(new_name)
            LauncherConfig.version["profile"] = new_name
            save_version()
        list_profiles.configure(values=list_dir())
        add_profile_Entry.delete(0, ctk.END)
        add_profile_Entry.lower()
        del_profile_button.configure(
            text=language_manager.get("settings.4_page.delete"),
            command=del_profile
        )
        add_profile_button.configure(
            text=language_manager.get("settings.4_page.add"),
            command=fun_add_profile
        )
        list_profiles.configure(state="readonly")
        list_profiles.set(new_name)
        rename_profile_button.configure(state="normal")
        open_profile.configure(state="normal")


def fun_rename_profile():
    current = list_profiles.get()
    if current != language_manager.get("settings.4_page.no"):
        add_profile_Entry.lift()
        add_profile_Entry.insert(0, current)
        rename_profile_button.configure(state="disabled")
        list_profiles.configure(state="disabled")
        open_profile.configure(state="disabled")
        del_profile_button.configure(
            text=language_manager.get("messages.answers.no"),
            command=_add_profile
        )
        add_profile_button.configure(
            text=language_manager.get("settings.4_page.save"),
            command=lambda: rename_profile(current)
        )


def open_folder_profile():
    current = list_profiles.get()
    if current != language_manager.get("settings.4_page.no"):
        path = os.path.join(LaunchOptions.minecraft_path, "profiles", "profile_" + current)
        log(f"Открытие папки профиля: {path}")
        os.startfile(path)
