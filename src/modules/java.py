def get_java_path() -> str | bool:
    """
    Retrieves the path to the installed Java runtime within the Minecraft directory.
    Returns False if no JVM runtime is installed.
    """
    jvm_installed = mcl.runtime.get_installed_jvm_runtimes(minecraft_path)
    if not jvm_installed:
        return False
    jvm_installed = jvm_installed[0]
    return os.path.join(minecraft_path, "runtime", jvm_installed, "windows-x64", jvm_installed, "bin", "java.exe")


def get_formatted_java_info(path: str) -> str | None:
    """
    Returns a formatted string containing Java vendor, version, LTS status and release date.
    Returns None if path is invalid or Java check fails.
    """
    if not path or not check_java(path):
        return
    output = None
    for flag in ("--version", "-version"):
        try:
            res = subprocess.run([path, flag], capture_output=True, text=True, check=True)
            output = (res.stdout or res.stderr).strip()
            break
        except subprocess.CalledProcessError as e:
            output = (e.stdout or e.stderr).strip()
            if flag == "-version":
                break

    if not output:
        return ""

    first_line = output.splitlines()[0]
    low = first_line.lower()

    # Determine Java vendor based on output
    if "openjdk" in low:
        vendor = "OpenJDK"
    elif "java version" in low:
        vendor = "Oracle Java"
    else:
        vendor = "Java"

    # Extract version and date information using regex
    m_ver = re.search(r"(\d+)(?:\.(\d+)(?:\.(\d+))?)?", first_line)
    m_date = re.search(r"(\d{4}-\d{2}-\d{2})", first_line)
    is_lts = "lts" in low

    if not m_ver:
        return f"{vendor}: {first_line}"

    major = int(m_ver.group(1))
    if major == 1 and m_ver.group(2):
        major = int(m_ver.group(2))
    parts = [m_ver.group(i) for i in range(1, 4) if m_ver.group(i)]
    full_ver = ".".join(parts)

    release_date = None
    if m_date:
        try:
            d = datetime.strptime(m_date.group(1), "%Y-%m-%d")
            release_date = d.strftime("%Y-%m-%d")
        except ValueError:
            release_date = m_date.group(1)

    # Construct formatted Java info string
    formatted_parts = [vendor]
    if full_ver:
        formatted_parts.append(full_ver)
    if is_lts:
        formatted_parts.append("LTS")
    if release_date:
        formatted_parts.append(f"({release_date})")

    return " ".join(formatted_parts)


def select_java_path() -> str | None:
    """
    Opens a file dialog to allow the user to select a Java executable file.
    Returns the selected file path or None if no file was selected.
    """
    file_path = filedialog.askopenfilename(
        title=language_manager.get("settings.2_page.select_java"),
        filetypes=[(language_manager.get("settings.2_page.java_exe"), "java.exe")]
    )

    if file_path:
        return file_path


def check_java(java_path: str) -> bool:
    """
    Checks whether the specified java executable path points to a valid Java runtime.
    Returns True if Java version command succeeds, False otherwise.
    """
    try:
        result = subprocess.run([java_path, '-version'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode == 0:
            return True
    except Exception:
        return False

    try:
        result = subprocess.run([java_path, '--version'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode == 0:
            return True
    except Exception:
        return False

    return False


def add_java():
    """
    Allows user to add a new Java path by selecting an executable and
    storing its formatted info and path into the config.
    Updates the Java selection combobox accordingly.
    """
    path = select_java_path()
    info = get_formatted_java_info(path)
    if info:
        config["java_paths"][info] = path
        save_config(config)
        java_combobox.configure(values=[language_manager.get("settings.2_page.recommended_java")] + list(config["java_paths"].keys()) + [language_manager.get("settings.2_page.add")])
    elif path:
        new_message(
            title=language_manager.get("messages.titles.error"),
            message=language_manager.get("messages.texts.error.java"),
            icon="cancel",
            option_1=language_manager.get("messages.answers.ok")
        )


def on_select_java(name: str):
    """
    Handles user selection from the Java combobox.
    If user selects 'Add', triggers add_java().
    Otherwise, updates config with selected Java path.
    """
    if name == language_manager.get("settings.2_page.add"):
        java_combobox.set(config["java"] or language_manager.get("settings.2_page.recommended_java"))
        add_java()
        return
    elif name == language_manager.get("settings.2_page.recommended_java"):
        config["java"] = default_config["java"]
    else:
        config["java"] = name
    save_config(config)


def del_java():
    """
    Deletes the currently selected custom Java path from config after confirmation.
    Resets selection to recommended Java if deletion confirmed.
    """
    current = java_combobox.get()
    if current == language_manager.get("settings.2_page.recommended_java"):
        return
    new_message(
        title=language_manager.get("messages.titles.warning"),
        message=f"{language_manager.get('messages.texts.warning.java')} ({current})",
        icon="question",
        option_1=language_manager.get("messages.answers.no"),
        option_2=language_manager.get("messages.answers.yes")
    )
    if msg.get() == language_manager.get("messages.answers.yes"):
        config["java"] = default_config["java"]
        config["java_paths"].pop(current)
        save_config(config)
        java_combobox.set(language_manager.get("settings.2_page.recommended_java"))
        java_combobox.configure(values=[language_manager.get("settings.2_page.recommended_java")] + list(config["java_paths"].keys()) + [language_manager.get("settings.2_page.add")])
