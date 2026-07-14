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
        return

    if is_java:
        log(f"Добавление Java установки: {path}")
        LauncherConfig.config["java_paths"].append(path)
        save_config()
        java_combobox.configure(values=get_java_options())
    elif path:
        log(f"Не удалось добавить Java установку: {path}", level="ERROR")
        ToastNotification(
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
    elif name == language_manager.get("settings.2_page.latest_java"):
        LauncherConfig.config["java"] = "Latest"
    else:
        LauncherConfig.config["java"] = name
    save_config()


def del_java():
    current = java_combobox.get()
    if current in (language_manager.get("settings.2_page.recommended_java"), language_manager.get("settings.2_page.latest_java")):
        return
    new_message(
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


class JavaRuntimeManager:
    @staticmethod
    def get_available_major_versions():
        api_url = "https://api.adoptium.net/v3/info/available_releases"

        try:
            r = requests.get(
                api_url,
                headers={"User-Agent": LauncherConfig.USER_AGENT},
                timeout=5
            )
            r.raise_for_status()

            data = r.json()
            versions = data["available_lts_releases"]

            LaunchOptions.available_major_versions = sorted(list(set(versions)))

        except Exception:
            LaunchOptions.available_major_versions = [8, 11, 17, 21, 25]

        java_combobox.configure(values=get_java_options())

    @staticmethod
    def get_latest_java(version):
        api_url = (
            f"https://api.adoptium.net/v3/assets/latest/{version}/hotspot"
            f"?architecture=x64&image_type=jre&os=windows&vendor=eclipse"
        )

        r = requests.get(
            api_url,
            headers={"User-Agent": LauncherConfig.USER_AGENT},
            timeout=5
        )
        r.raise_for_status()

        data = r.json()
        if not data:
            return None, None

        latest_release = data[0]

        semver = latest_release["version"]["semver"]
        download_url = latest_release["binary"]["package"]["link"]

        return semver, download_url

    @staticmethod
    def _get_local_semantic_version(target_java_dir):
        release_path = os.path.join(target_java_dir, "release")
        if not os.path.exists(release_path):
            return None

        try:
            with open(release_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("SEMANTIC_VERSION="):
                        return line.split("=", 1)[1].strip().strip('"')
        except Exception:
            return None

        return None

    @staticmethod
    def _save_local_semantic_version(target_java_dir, semver):
        try:
            os.makedirs(target_java_dir, exist_ok=True)
            with open(os.path.join(target_java_dir, "release"), "w", encoding="utf-8") as f:
                f.write(f'SEMANTIC_VERSION="{semver}"\n')
        except Exception:
            pass

    @staticmethod
    def download_and_extract_java(version, callback=None):
        runtimes_dir = os.path.join(LaunchOptions.minecraft_path, "runtime")
        target_java_dir = os.path.join(runtimes_dir, f"Java {version}")

        api_semver, download_url = JavaRuntimeManager.get_latest_java(version)
        if not api_semver or not download_url:
            return target_java_dir if os.path.exists(target_java_dir) else None

        local_semver = JavaRuntimeManager._get_local_semantic_version(target_java_dir)

        java_exe_path = os.path.join(target_java_dir, "bin", "java.exe")
        if local_semver == api_semver and os.path.exists(java_exe_path):
            return os.path.abspath(target_java_dir)

        zip_filename = "java_temp.zip"

        os.makedirs(runtimes_dir, exist_ok=True)
        callback["setStatus"](language_manager.get("main.mcl_status.install_java_runtime"))

        with requests.get(
                download_url,
                stream=True,
                timeout=300,
                headers={"User-Agent": LauncherConfig.USER_AGENT}
        ) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", 0))
            if callback and "setMax" in callback:
                callback["setMax"](total_size)
            downloaded = 0
            with open(zip_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if callback and "setProgress" in callback:
                            callback["setProgress"](downloaded)

        if os.path.exists(target_java_dir):
            shutil.rmtree(target_java_dir)

        with zipfile.ZipFile(zip_filename, "r") as zip_ref:
            for member in zip_ref.infolist():
                filename = member.filename.strip()
                norm_path = os.path.normpath(filename)
                path_parts = norm_path.split(os.sep)

                if len(path_parts) <= 1:
                    continue

                relative_path = os.path.join(*path_parts[1:])
                final_path = os.path.join(target_java_dir, relative_path)

                if member.is_dir():
                    os.makedirs(final_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(final_path), exist_ok=True)
                    with zip_ref.open(member) as src, open(final_path, "wb") as dst:
                        shutil.copyfileobj(src, dst)

        JavaRuntimeManager._save_local_semantic_version(target_java_dir, api_semver)

        return os.path.abspath(target_java_dir)

    @staticmethod
    def get_all_javas_exe():
        runtimes_dir = os.path.join(LaunchOptions.minecraft_path, "runtime")

        java_exes = []

        for entry in os.listdir(runtimes_dir):
            java_exe = os.path.join(runtimes_dir, entry, "bin", "java.exe")
            if os.path.exists(java_exe):
                java_exes.append(os.path.abspath(java_exe))

        return java_exes

    @staticmethod
    def get_any_java_exe(version):
        runtimes_dir = os.path.join(LaunchOptions.minecraft_path, "runtime")

        java_exe = os.path.join(runtimes_dir, f"Java {version}", "bin", "java.exe")
        if os.path.exists(java_exe):
            return os.path.abspath(java_exe)

        return None
