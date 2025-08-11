def profile_select(*args):
    """
    Handles profile selection from the dropdown. 
    Updates the version dict depending on the selected profile.
    """
    current = list_profiles.get()
    version["profile"] = False if current == language_manager.get("settings.4_page.no") else current
    save_version(version)


def del_profile():
    """
    Deletes the currently selected profile after confirmation from the user.
    Updates the UI and version dict accordingly.
    """
    current = list_profiles.get()
    if current != language_manager.get("settings.4_page.no"):
        new_message(
            title=language_manager.get("messages.titles.warning"),
            message=f"{language_manager.get('messages.texts.warning.profile')} ({current})",
            icon="question",
            option_1=language_manager.get("messages.answers.no"),
            option_2=language_manager.get("messages.answers.yes")
        )
        if msg.get() == language_manager.get("messages.answers.yes"):
            if os.path.isdir(os.path.join(minecraft_path, "profiles", "profile_" + current)):
                shutil.rmtree(os.path.join(minecraft_path, "profiles", "profile_" + current))

            list_profiles.configure(values=list_dir())
            first = list_profiles.cget("values")[0] if list_profiles.cget("values")[0] != "" else language_manager.get("settings.4_page.no")
            list_profiles.set(first)
            version["profile"] = False if first == language_manager.get("settings.4_page.no") else first
            save_version(version)


def _add_profile():
    """
    Resets UI elements after adding a new profile or cancelling add action.
    """
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
    """
    Saves a new profile based on user input. 
    Creates corresponding folder and updates UI and version dict.
    """
    name = add_profile_Entry.get().strip()
    no = language_manager.get("settings.4_page.no")
    if not name or name == no:
        return

    try:
        profile_path = os.path.join(minecraft_path, "profiles", "profile_" + name)
        os.makedirs(profile_path)
        # List of required Minecraft directories
        dirs = ["assets", "bin", "libraries", "logs", "resourcepacks", "saves",
                "screenshots", "shaderpacks", "versions", "profiles", "mods"]
    
        # Create directories if they don't exist
        for directory in dirs:
            os.makedirs(os.path.join(profile_path, directory), exist_ok=True)
    except Exception as e:
        excepthook(*sys.exc_info())
        new_message(
            title=language_manager.get("messages.titles.error"),
            message=language_manager.get("messages.texts.error.profile_add") + str(e),
            icon="cancel",
            option_1=language_manager.get("messages.answers.ok")
        )
    else:
        if list_profiles.cget("values") == (no,):
            version["profile"] = name
            list_profiles.set(name)
            save_version(version)
        list_profiles.configure(state="readonly")
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
    """
    Prepares the UI for adding a new profile. 
    Temporarily disables unrelated UI elements.
    """
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
    """
    Returns a list of existing profile names.
    Adds a "no profile" option as the first element.
    """
    profiles_dir = os.path.join(minecraft_path, "profiles")
    return [language_manager.get("settings.4_page.no")] + [
        g[8:] for g in os.listdir(profiles_dir) if len(g) >= 9 and os.path.isdir(os.path.join(profiles_dir, g))
    ]

def rename_profile(old_name: str):
    """
    Renames an existing profile folder.
    
    Args:
        old_name (str): Current name of the profile.
    """
    new_name = add_profile_Entry.get().strip()
    no = language_manager.get("settings.4_page.no")
    if not new_name or new_name == old_name or new_name == no:
        return

    try:
        os.rename(
            os.path.join(minecraft_path, "profiles", "profile_" + old_name),
            os.path.join(minecraft_path, "profiles", "profile_" + new_name)
        )
    except Exception as e:
        excepthook(*sys.exc_info())
        new_message(
            title=language_manager.get("messages.titles.error"),
            message=language_manager.get("messages.texts.error.profile_rename") + str(e),
            icon="cancel",
            option_1=language_manager.get("messages.answers.ok")
        )
    else:
        if version["profile"] == old_name:
            list_profiles.set(new_name)
            version["profile"] = new_name
            save_version(version)
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
    """
    Prepares the UI to rename the currently selected profile.
    """
    current = list_profiles.get()
    if current != language_manager.get("settings.4_page.no"):
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
            command=lambda: rename_profile(current)
        )


def open_folder_profile():
    """
    Opens the folder of the currently selected profile in the system's file explorer.
    """
    current = list_profiles.get()
    if current != language_manager.get("settings.4_page.no"):
        path = os.path.join(minecraft_path, "profiles", "profile_" + current)
        os.startfile(path)
