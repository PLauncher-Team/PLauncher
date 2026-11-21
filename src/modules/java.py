from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


def get_java_path() -> str | bool:
    jvm_installed = mcl.runtime.get_installed_jvm_runtimes(LaunchOptions.minecraft_path)
    if not jvm_installed:
        return False
    jvm_installed = jvm_installed[0]
    java_path = mcl.runtime.get_executable_path(jvm_installed, LaunchOptions.minecraft_path)
    return java_path


def select_java_path() -> str:
    file_path = filedialog.askopenfilename(
        title=language_manager.get("settings.2_page.select_java"),
        filetypes=[(language_manager.get("settings.2_page.java_exe"), "java.exe")]
    )

    return file_path


def check_java(java_path: str) -> bool:
    try:
        result = subprocess.run([java_path, '-version'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode == 0:
            return True
    except Exception:
        pass

    try:
        result = subprocess.run([java_path, '--version'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode == 0:
            return True
    except Exception:
        pass

    return False


def add_java():
    path = select_java_path()
    is_java = check_java(path)
    if os.path.normcase(path) in map(os.path.normcase, LauncherConfig.config["java_paths"] + JavaRuntimeManager.get_all_javas_exe()):
        log(f"Java установка уже существует: {path}", "WARNING")
        return

    if is_java:
        log(f"Добавление Java установки: {path}")
        LauncherConfig.config["java_paths"].append(path)
        save_config()
        java_combobox.configure(values=get_java_options())
    elif path:
        log(f"Не удалось добавить Java установку: {path}", level="ERROR")
        ToastNotification(master=root, 
            title=language_manager.get("messages.titles.error"),
            message=language_manager.get("messages.texts.error.java"),
            toast_type="error"
        )


def on_select_java(name: str):
    if name == language_manager.get("settings.2_page.add"):
        if LauncherConfig.config["java"] == "Stable":
            java_combobox.set(language_manager.get("settings.2_page.recommended_java"))
        elif LauncherConfig.config["java"] == "Latest":
            java_combobox.set(language_manager.get("settings.2_page.latest_java"))
        else:
            java_combobox.set(LauncherConfig.config["java"])
        add_java()
        return
    elif name == language_manager.get("settings.2_page.recommended_java"):
        LauncherConfig.config["java"] = "Stable"
        log(f"Выбрана рекомендуемая Java версия")
    elif name == language_manager.get("settings.2_page.latest_java"):
        LauncherConfig.config["java"] = "Latest"
        log(f"Выбрана последняя Java версия")
    else:
        LauncherConfig.config["java"] = name
        log(f"Выбрана Java: {name}")
    save_config()


def del_java():
    current = java_combobox.get()
    if current in (language_manager.get("settings.2_page.recommended_java"), language_manager.get("settings.2_page.latest_java")):
        return
    new_message(master=root, 
        title=language_manager.get("messages.titles.warning"),
        message=f"{language_manager.get('messages.texts.warning.java')} ({current})",
        icon="question",
        option_1=language_manager.get("messages.answers.no"),
        option_2=language_manager.get("messages.answers.yes")
    )
    if GuiOptions.msg.get() == language_manager.get("messages.answers.yes"):
        log(f"Удаление Java установки: {current}")
        LauncherConfig.config["java"] = default_config["java"]
        LauncherConfig.config["java_paths"].remove(current)
        save_config()
        java_combobox.set(language_manager.get("settings.2_page.latest_java"))
        java_combobox.configure(values=get_java_options())


def get_java_options():
    return [language_manager.get("settings.2_page.latest_java")] + [language_manager.get("settings.2_page.recommended_java")] + LauncherConfig.config["java_paths"] + [f"Java {i}" for i in LaunchOptions.available_major_versions] + [language_manager.get("settings.2_page.add")]


