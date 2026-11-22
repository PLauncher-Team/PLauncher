from typing import Any

from .. import ui_support
from ..ui_support import *
from .notifications import *
from .mods.manager import ModManager
from .mods.view import ModViewer

def configure(**dependencies: Any) -> None:
    globals().update(dependencies)


def initialize_gui() -> dict[str, Any]:
    
    def show_error_notification(title: str, message: str) -> None:
        ToastNotification(master=root, title=title, message=message, toast_type="error")
    
    def confirm_java_deletion(name: str) -> bool:
        yes = language_manager.get("messages.answers.yes")
        new_message(
            master=root,
            title=language_manager.get("messages.titles.warning"),
            message=f"{language_manager.get('messages.texts.warning.java')} ({name})",
            icon="question",
            option_1=language_manager.get("messages.answers.no"),
            option_2=yes,
        )
        return GuiOptions.msg.get() == yes
    
    ctk.set_appearance_mode("Dark")
    if LauncherConfig.config["custom_theme"]:
        theme_path = LauncherConfig.config["custom_theme"]
    else:
        themes = []
        for filename in os.listdir("themes"):
            full_path = os.path.join("themes", filename)
            if os.path.isfile(full_path):
                name_without_ext = os.path.splitext(filename)[0]
                themes.append(name_without_ext)
        theme_path = random.choice(themes)
    log(f"Тема лаунчера: {theme_path}")
    ctk.set_default_color_theme(f"themes/{theme_path}.json")
    
    root = ctk.CTk(fg_color="#242424")
    
    root.report_callback_exception = excepthook
    root.resizable(False, False)
    root.geometry(f"{1000}x{562}+{center(root, 1000, 562)}")
    root.protocol("WM_DELETE_WINDOW", ex)
    root.title("PLauncher")
    
    if not LauncherConfig.config["random_theme"]:
        selected_theme = LauncherConfig.config["selected_theme"]
    else:
        selected_theme = random.randint(1, 5)
    color_selected = selected_theme - 1
    
    if LauncherConfig.config["custom_image"]:
        image_path = LauncherConfig.config["custom_image"]
    else:
        image_path = os.path.join("png", "dark", f"{selected_theme}.png")
    
    GuiOptions = GuiOption()
    
    log(f"Изображение лаунчера: {image_path}")
    
    pil_image = PIL.Image.open(image_path)
    ctk_image = ctk.CTkImage(pil_image, size=(1000, 562))
    label = ctk.CTkLabel(root, image=ctk_image)
    label.place(relheight=1, relwidth=1)
    
    crash_window = CrashLogWindow(
        root,
        language_manager=language_manager,
        language=language,
        online=LauncherConfig.IS_INTERNET,
        analyzer=log_analyzer,
        logger=log,
        exception_handler=excepthook,
        kill_thread=kill_thread,
        center_window=center,
        titlebar_helper=hPyT,
        titlebar_color=GuiOptions.fg_color,
        header_color_setter=pywinstyles.change_header_color,
    )
    mod_viewer_window = ModViewer(root)
    
    release_var = ctk.BooleanVar(value=LauncherConfig.config["release"])
    snapshot_var = ctk.BooleanVar(value=LauncherConfig.config["snapshot"])
    old_beta_var = ctk.BooleanVar(value=LauncherConfig.config["old_beta"])
    old_alpha_var = ctk.BooleanVar(value=LauncherConfig.config["old_alpha"])
    default_var = ctk.BooleanVar(value=LauncherConfig.config["default_path"])
    hide_var = ctk.BooleanVar(value=LauncherConfig.config["hide"])
    debug_var = ctk.BooleanVar(value=LauncherConfig.config["debug"])
    check_var = ctk.BooleanVar(value=LauncherConfig.config["check_files"])
    ely_by_var = ctk.BooleanVar(value=LauncherConfig.config["ely_by"])
    default_skin_var = ctk.BooleanVar(value=LauncherConfig.config["default_skin"])
    
    version_frame = VersionFrame(root)
    version_frame.place(relwidth=0.175, relheight=0.177, relx=0.797, rely=0.05)
    blackout_frame = ctk.CTkFrame(root, fg_color="black")
    blackout_frame.place(relwidth=1, relheight=1)
    pywinstyles.set_opacity(blackout_frame, value=0)
    blackout_frame.bind("<Button-1>", lambda a: settings_controller.close_settings())
    
    settings_frame = ctk.CTkFrame(root, fg_color=GuiOptions.fg_color)
    settings_frame.place(relwidth=0.45, relheight=1, relx=1)
    pywinstyles.set_opacity(settings_frame, value=0.9)
    
    header_frame = ctk.CTkFrame(settings_frame, corner_radius=0)
    header_frame.place(relx=0, rely=0, relwidth=1, relheight=0.1)
    back_btn = ctk.CTkButton(
        header_frame,
        text="<",
        command=lambda: settings_controller.close_settings(),
        font=("Segoe UI", 13)
    )
    back_btn.place(relx=0.914, rely=0.5, relwidth=0.066, relheight=0.533, anchor="w")
    
    title_label = ctk.CTkLabel(
        header_frame,
        text=language_manager.get("settings.title"),
        font=("Segoe UI", 23, "bold")
    )
    title_label.place(relx=0.05, rely=0.5, anchor="w")
    
    
    tabs = language_manager.get("settings.pages")
    tab_switch = ctk.CTkSegmentedButton(
        settings_frame,
        values=tabs,
        font=("Segoe UI", 13),
        command=lambda name: settings_controller.show_tab(name),
        border_width=0,
        corner_radius=0
    
    )
    tab_switch.place(relx=0.005, rely=0.1, relwidth=0.99, relheight=0.1)
    
    tab_switch._buttons_dict[tabs[4]].configure(state="disabled")
    
    content_frames = {}
    for name in tabs:
        frame = ctk.CTkFrame(settings_frame, fg_color=GuiOptions.fg_color)
        content_frames[name] = frame
    
    settings_controller = SettingsController(
        blackout_frame=blackout_frame,
        settings_frame=settings_frame,
        root=root,
        gui_options=GuiOptions,
        content_frames=content_frames,
        fps=LauncherConfig.FPS,
        opacity_setter=pywinstyles.set_opacity,
        version_filter_vars=(release_var, snapshot_var, old_beta_var, old_alpha_var),
        previous_version_filters=lambda: LaunchOptions.old_types_versions,
        load_versions=load_versions,
    )
    settings_controller.show_tab(tabs[0])
    tab_switch.set(tabs[0])
    ctk.CTkLabel(
        content_frames[tabs[0]],
        text=language_manager.get("settings.1_page.version_types_1"),
        font=("Segoe UI", 15, "bold")
    ).place(relwidth=0.9, relx=0.05, rely=0.005)
    
    ctk.CTkLabel(
        content_frames[tabs[0]],
        text=language_manager.get("settings.1_page.version_types_2"),
        font=("Segoe UI", 12, "bold"),
        anchor="w",
    ).place(relwidth=0.9, relx=0.05, rely=0.063)
    
    release_checkbox = ctk.CTkCheckBox(
        content_frames[tabs[0]],
        text=language_manager.get("settings.1_page.release"),
        variable=release_var,
        command=save_versions_var,
        font=("Segoe UI", 13)
    )
    release_checkbox.place(relx=0.05, rely=0.124)
    
    snapshot_checkbox = ctk.CTkCheckBox(
        content_frames[tabs[0]],
        text=language_manager.get("settings.1_page.snapshots"),
        variable=snapshot_var,
        command=save_versions_var,
        font=("Segoe UI", 13)
    )
    snapshot_checkbox.place(relx=0.572, rely=0.124)
    
    old_beta_check = ctk.CTkCheckBox(
        content_frames[tabs[0]],
        text=language_manager.get("settings.1_page.old_beta"),
        variable=old_beta_var,
        command=save_versions_var,
        font=("Segoe UI", 13)
    )
    old_beta_check.place(relx=0.05, rely=0.19)
    
    old_alpha_check = ctk.CTkCheckBox(
        content_frames[tabs[0]],
        text=language_manager.get("settings.1_page.old_alpha"),
        variable=old_alpha_var,
        command=save_versions_var,
        font=("Segoe UI", 13)
    )
    old_alpha_check.place(relx=0.572, rely=0.19)
    
    ctk.CTkLabel(
        content_frames[tabs[0]],
        text=language_manager.get("settings.1_page.installed_versions"),
        font=("Segoe UI", 15, "bold"),
    ).place(relwidth=0.9, relx=0.05, rely=0.331)
    
    ctk.CTkLabel(
        content_frames[tabs[0]],
        text=language_manager.get("settings.1_page.manager_versions"),
        font=("Segoe UI", 12, "bold"),
        anchor="w",
    ).place(relwidth=0.9, relx=0.05, rely=0.392)
    
    installed_versions_combobox_ctk = ctk.CTkComboBox(
        content_frames[tabs[0]],
        state="readonly",
        font=("Segoe UI", 13),
        height=0.083 * 393
    )
    installed_versions_combobox_ctk.place(relwidth=0.82, relx=0.05, rely=0.453)
    
    installed_versions_combobox = CTkScrollableDropdown(
        installed_versions_combobox_ctk,
        values=[],
        justify="left",
        scrollbar_button_color=GuiOptions.fg_color,
        scrollbar_button_hover_color=GuiOptions.hover_color,
        pagination=False,
        font=("Segoe UI", 13),
        multiple=True
    )
    
    del_version = ctk.CTkButton(
        content_frames[tabs[0]],
        text="-",
        command=del_installed_version,
        hover_color="red",
        font=("Segoe UI", 13)
    )
    del_version.place(relwidth=0.079, relheight=0.081, relx=0.871, rely=0.453)
    
    ctk.CTkLabel(
        content_frames[tabs[0]],
        text=language_manager.get("settings.1_page.other_settings"),
        font=("Segoe UI", 15, "bold"),
    ).place(relwidth=0.9, relheight=0.087, relx=0.05, rely=0.623)
    
    texts_language = language_manager.get_languages_names()
    
    language_choice = ctk.CTkSegmentedButton(content_frames[tabs[0]],
                                             values=list(texts_language.values()),
                                             command=select_language,
                                             font=("Segoe UI", 13))
    language_choice.place(relwidth=0.9, relx=0.05, relheight=0.087, rely=0.714)
    language_choice.set(texts_language[language_manager.language])
    
    hide_checkbox = ctk.CTkCheckBox(
        content_frames[tabs[0]],
        text=language_manager.get("settings.1_page.hide_launcher"),
        variable=hide_var,
        command=lambda: save_set("hide", hide_var.get()),
        font=("Segoe UI", 13)
    )
    hide_checkbox.place(relx=0.05, rely=0.818)
    
    check_files = ctk.CTkCheckBox(
        content_frames[tabs[0]],
        text=language_manager.get("settings.1_page.check_files"),
        command=lambda: save_set("check_files", check_var.get()),
        variable=check_var,
        font=("Segoe UI", 13)
    )
    check_files.place(relx=0.05, rely=0.89)
    
    ctk.CTkLabel(
        content_frames[tabs[1]],
        text=language_manager.get("settings.2_page.java_settings"),
        font=("Segoe UI", 15, "bold"),
    ).place(relwidth=0.9, rely=0.005, relx=0.05)
    
    ctk.CTkLabel(
        content_frames[tabs[1]],
        text=language_manager.get("settings.2_page.java_used"),
        font=("Segoe UI", 12, "bold"),
        anchor="w",
    ).place(relwidth=0.9, relx=0.05, rely=0.063)
    
    java_combobox = ctk.CTkComboBox(
        content_frames[tabs[1]],
        values=[language_manager.get("settings.2_page.latest_java")] + [language_manager.get("settings.2_page.recommended_java")] + LauncherConfig.config["java_paths"] + [language_manager.get("settings.2_page.add")],
        state="readonly",
        command=lambda name: java_controller.on_select_java(name),
        font=("Segoe UI", 13),
        height=0.083 * 393
    )
    java_combobox.place(relwidth=0.82, relx=0.05, rely=0.124)
    if LauncherConfig.config["java"] == "Stable":
        java_combobox.set(language_manager.get("settings.2_page.recommended_java"))
    elif LauncherConfig.config["java"] == "Latest":
        java_combobox.set(language_manager.get("settings.2_page.latest_java"))
    else:
        java_combobox.set(LauncherConfig.config["java"])
    
    del_java_button = ctk.CTkButton(
        content_frames[tabs[1]],
        text="-",
        command=lambda: java_controller.delete_java(),
        hover_color="red",
        font=("Segoe UI", 13)
    )
    del_java_button.place(relwidth=0.079, relheight=0.081, relx=0.871, rely=0.124)
    
    java_controller = JavaController(
        settings=LauncherConfig.config,
        java_runtime=java_runtime_service,
        available_major_versions=lambda: LaunchOptions.available_major_versions,
        launcher_api=mcl,
        minecraft_directory=lambda: LaunchOptions.minecraft_path,
        language_manager=language_manager,
        java_selector=java_combobox,
        file_dialog=filedialog,
        process_api=subprocess,
        save_settings=save_config,
        logger=log,
        notify_error=show_error_notification,
        confirm_delete=confirm_java_deletion,
    )
    
    ctk.CTkLabel(
        content_frames[tabs[1]],
        text=language_manager.get("settings.2_page.amt_memory"),
        font=("Segoe UI", 12, "bold"),
        anchor="w",
    ).place(relwidth=0.9, relx=0.05, rely=0.207)
    
    memory_options = create_memory_options()
    selected_memory = ctk.StringVar(root)
    selected_memory.set(LauncherConfig.config["memory_args"])
    
    memory_combobox = ctk.CTkComboBox(
        content_frames[tabs[1]],
        variable=selected_memory,
        values=memory_options,
        command= lambda value: on_select(value),
        font=("Segoe UI", 13),
        height=0.083 * 393
    )
    
    vcmd = (
        memory_combobox.register(validate_memory),
        "%P",
    )
    
    memory_combobox._entry.configure(
        validate="all",
        validatecommand=vcmd
    )
    
    memory_combobox.place(relwidth=0.9, relx=0.05, rely=0.268)
    
    ctk.CTkLabel(
        content_frames[tabs[1]],
        text=language_manager.get("settings.2_page.args_JVM"),
        font=("Segoe UI", 12, "bold"),
        anchor="w",
    ).place(relwidth=0.9, relx=0.05, rely=0.351)
    
    args_entry = ctk.CTkEntry(
        content_frames[tabs[1]],
        font=("Segoe UI", 13),
    )
    args_entry.insert(0, LauncherConfig.config["custom_args"])
    args_entry.bind("<KeyRelease>", lambda h: entry_input())
    args_entry.place(relwidth=0.9, relx=0.05, relheight=0.083, rely=0.412)
    
    ctk.CTkLabel(
        content_frames[tabs[1]],
        text=language_manager.get("settings.2_page.game_directory"),
        font=("Segoe UI", 15, "bold"),
    ).place(relwidth=0.9, relx=0.05, rely=0.595)
    
    default_directory = ctk.CTkCheckBox(
        content_frames[tabs[1]],
        text=language_manager.get("settings.2_page.default_path"),
        variable=default_var,
        font=("Segoe UI", 13)
    )
    default_directory.configure(
        command=lambda: change_mine(False)
    )
    default_directory.place(relx=0.05, rely=0.658)
    
    current_folder = ctk.CTkLabel(
        content_frames[tabs[1]],
        text=language_manager.get("settings.2_page.current_path") + LaunchOptions.minecraft_path,
        font=("Segoe UI", 12),
    )
    current_folder.place(relwidth=0.9, relx=0.05, rely=0.9)
    
    open_folder = ctk.CTkButton(
        content_frames[tabs[1]],
        text=language_manager.get("settings.2_page.open_folder"),
        font=("Segoe UI", 20, "bold"),
        command=lambda: os.startfile(LaunchOptions.minecraft_path),
    )
    open_folder.place(relwidth=0.69, relheight=0.15, relx=0.05, rely=0.734)
    
    change_folder = ctk.CTkButton(
        content_frames[tabs[1]],
        text=language_manager.get("settings.2_page.change_folder"),
        font=("Segoe UI", 13, "bold"),
    )
    if LauncherConfig.config["default_path"]:
        change_folder.configure(state="disabled")
    change_folder.place(relwidth=0.205, relheight=0.15, relx=0.745, rely=0.734)
    change_folder.configure(
        command=change_mine
    )
    
    frame_skin = ctk.CTkFrame(content_frames[tabs[2]], fg_color="transparent")
    frame_skin.place(relwidth=1, relheight=0.6)
    frame_skin.update_idletasks()
    label_skin = ctk.CTkLabel(frame_skin)
    label_skin.place(relheight=0.9, relx=0.5, rely=0.5, anchor="center")
    
    update_skin_button = ctk.CTkButton(
        frame_skin,
        text=language_manager.get("settings.3_page.update"),
        font=("Segoe UI", 20),
        command=lambda: threading.Thread(target=skin_controller.set_skin).start(),
    )
    update_skin_button.place(relx=0.98, rely=0.97, relwidth=0.4, relheight=0.15, anchor="se")
    pywinstyles.set_opacity(update_skin_button, color="#242424")
    
    select_skin_button = ctk.CTkButton(
        content_frames[tabs[2]],
        text=language_manager.get("settings.3_page.select_file_skin"),
        font=("Segoe UI", 20, "bold"),
        command=lambda: skin_controller.select_skin_file(),
    )
    select_skin_button.place(rely=0.61, relx=0.05, relheight=0.15, relwidth=0.9)
    
    skins_ely_by_checkbox = ctk.CTkCheckBox(
        content_frames[tabs[2]],
        text=language_manager.get("settings.3_page.use_ely_by"),
        command=lambda: [save_set("ely_by", ely_by_var.get()), skin_controller.update_controls(), threading.Thread(target=skin_controller.set_skin).start()],
        variable=ely_by_var,
        font=("Segoe UI", 13),
    )
    skins_ely_by_checkbox.place(relx=0.05, rely=0.78)
    
    skins_default_checkbox = ctk.CTkCheckBox(
        content_frames[tabs[2]],
        text=language_manager.get("settings.3_page.use_default_skin"),
        command=lambda: [save_set("default_skin", default_skin_var.get()), skin_controller.update_controls(), threading.Thread(target=skin_controller.set_skin).start()],
        variable=default_skin_var,
        font=("Segoe UI", 13),
    )
    skins_default_checkbox.place(relx=0.05, rely=0.875)
    
    skin_controller = SkinController(
        settings=LauncherConfig.config,
        default_skin=default_config["custom_skin"],
        online=LauncherConfig.IS_INTERNET,
        username=lambda: username_entry.get(),
        skin_label=label_skin,
        update_button=update_skin_button,
        select_button=select_skin_button,
        ely_by_checkbox=skins_ely_by_checkbox,
        default_skin_variable=default_skin_var,
        ely_by_variable=ely_by_var,
        language_manager=language_manager,
        http_client=requests,
        file_dialog=filedialog,
        image_factory=lambda image: ctk.CTkImage(
            light_image=image, dark_image=image, size=image.size
        ),
        notify_error=show_error_notification,
        logger=log,
        save_config=save_config,
    )
    
    skin_controller.update_controls()
    
    chapter5 = ctk.CTkLabel(
        content_frames[tabs[3]],
        text=language_manager.get("settings.4_page.loaders_mods"),
        font=("Segoe UI", 15, "bold"),
    )
    chapter5.place(relwidth=0.9, relx=0.05, rely=0.005, relheight=0.086)
    
    choice_version_ctk = ctk.CTkComboBox(
        content_frames[tabs[3]],
        state="readonly",
        font=("Segoe UI", 13),
        height=393 * 0.083
    )
    choice_version_ctk.place(relwidth=0.627, relx=0.05, rely=0.099)
    choice_version = CTkScrollableDropdown(
        choice_version_ctk,
        values=[],
        justify="left",
        scrollbar_button_color=GuiOptions.fg_color,
        scrollbar_button_hover_color=GuiOptions.hover_color,
        height=562,
    )
    choice_version.search_entry.configure(corner_radius=20, border_width=0,
                                          font=("Segoe UI", 13),)
    choice_version.button_container.configure(border_width=0)
    choice_version.pagination_frame.configure(border_width=0)
    
    choice_loader = ctk.CTkComboBox(
        content_frames[tabs[3]],
        state="readonly",
        command=lambda loader: choice_version.configure(values=loader_controller.list_versions(loader)),
        values=[],
        font=("Segoe UI", 13),
        height=393 * 0.083
    )
    choice_loader.place(relwidth=0.272, relx=0.677, rely=0.099)
    
    progress_loader = ctk.CTkProgressBar(
        content_frames[tabs[3]],
    )
    progress_loader.place(relwidth=0.9, relx=0.05, relheight=0.087, rely=0.19)
    progress_loader.set(0)
    
    install_loader = ctk.CTkButton(
        content_frames[tabs[3]],
        text=language_manager.get("settings.4_page.install_loader"),
        font=("Segoe UI", 20, "bold"),
        command=lambda: threading.Thread(target=loader_controller.install_with_controls).start(),
    )
    install_loader.place(relwidth=0.9, relx=0.05, relheight=0.206, rely=0.285)
    
    chapter4 = ctk.CTkLabel(
        content_frames[tabs[3]],
        text=language_manager.get("settings.4_page.mods_profiles"),
        font=("Segoe UI", 15, "bold"),
    )
    chapter4.place(relwidth=0.9, relx=0.05, rely=0.543)
    
    list_profiles = ctk.CTkComboBox(
        content_frames[tabs[3]],
        state="readonly",
        values=[language_manager.get("settings.4_page.no")] + profile_service.list_profiles(),
        command=lambda _value: profile_controller.select_profile(),
        font=("Segoe UI", 13),
        border_width=0,
        height=393 * 0.083
    )
    if not LauncherConfig.version["profile"]:
        list_profiles.set(language_manager.get("settings.4_page.no"))
    else:
        list_profiles.set(LauncherConfig.version["profile"])
    list_profiles.place(relwidth=0.9, relx=0.05, rely=0.626)
    
    add_profile_Entry = ctk.CTkEntry(
        content_frames[tabs[3]],
        font=("Segoe UI", 13),
    )
    add_profile_Entry.place(relwidth=0.9, relx=0.05, relheight=0.083, rely=0.626)
    
    add_profile_button = ctk.CTkButton(
        content_frames[tabs[3]],
        text=language_manager.get("settings.4_page.add"),
        command=lambda: profile_controller.begin_add(),
        hover_color="green",
        font=("Segoe UI", 13),
    )
    add_profile_button.place(relwidth=0.3, relx=0.05, relheight=0.083, rely=0.71)
    
    del_profile_button = ctk.CTkButton(
        content_frames[tabs[3]],
        text=language_manager.get("settings.4_page.delete"),
        command=lambda: profile_controller.delete_current(),
        hover_color="red",
        font=("Segoe UI", 13),
    )
    del_profile_button.place(relwidth=0.3, relheight=0.083, relx=0.35, rely=0.71)
    
    rename_profile_button = ctk.CTkButton(
        content_frames[tabs[3]],
        text=language_manager.get("settings.4_page.change"),
        command=lambda: profile_controller.begin_rename(),
        font=("Segoe UI", 13),
    )
    rename_profile_button.place(relwidth=0.3, relheight=0.083, relx=0.65, rely=0.71)
    
    open_profile = ctk.CTkButton(
        content_frames[tabs[3]],
        text=language_manager.get("settings.4_page.open_folder"),
        font=("Segoe UI", 20, "bold"),
        command=lambda: profile_controller.open_folder(),
    )
    open_profile.place(relwidth=0.9, relx=0.05, relheight=0.156, rely=0.793)
    list_profiles.lift()
    
    def confirm_profile_deletion(name: str) -> bool:
        no = language_manager.get("messages.answers.no")
        yes = language_manager.get("messages.answers.yes")
        new_message(
            master=root,
            title=language_manager.get("messages.titles.warning"),
            message=f"{language_manager.get('messages.texts.warning.profile')} ({name})",
            icon="question",
            option_1=no,
            option_2=yes,
        )
        return GuiOptions.msg.get() == yes
    
    def notify_profile_error(title: str, message: str) -> None:
        ToastNotification(master=root, title=title, message=message, toast_type="error")
    
    profile_controller = ProfileController(
        profile_service=profile_service,
        language_manager=language_manager,
        profile_selector=list_profiles,
        name_entry=add_profile_Entry,
        add_button=add_profile_button,
        delete_button=del_profile_button,
        rename_button=rename_profile_button,
        open_button=open_profile,
        get_active_profile=lambda: LauncherConfig.version["profile"],
        set_active_profile=lambda value: LauncherConfig.version.__setitem__("profile", value),
        save_active_profile=save_version,
        confirm_delete=confirm_profile_deletion,
        notify_error=notify_profile_error,
        refresh_mod_viewer=lambda: setattr(mod_viewer_window, "_first_load_done", False),
        logger=log,
        open_path=lambda path: os.startfile(str(path)),
    )
    
    status_label = ctk.CTkLabel(
        root,
        text=language_manager.get("main.status.waiting"),
        font=("Segoe UI", 17, "bold"),
        anchor="s",
        fg_color="#242424",
        bg_color="#242424"
    )
    status_label.place(relx=0.671, rely=0.725, relwidth=0.313, relheight=0.074)
    pywinstyles.set_opacity(status_label, color="#242424")
    
    progress_bar = ctk.CTkProgressBar(
        root,
    )
    progress_bar.place(relx=0.675, rely=0.807, relwidth=0.305, relheight=0.021)
    progress_bar.set(0)
    pywinstyles.set_opacity(progress_bar, value=0.9)
    
    username_entry = ctk.CTkEntry(
        root,
        placeholder_text="Steve",
        font=("Segoe UI", 23),
    )
    username_entry.bind("<KeyRelease>", lambda h: save_config_menu())
    username_entry.insert(0, LauncherConfig.config["name"])
    username_entry.place(relx=0.015, rely=0.848, relwidth=0.313, relheight=0.124)
    pywinstyles.set_opacity(username_entry, color="#242424", value=0.9)
    
    pil_image_about_us = PIL.Image.open("png/GUI/feedback.png")
    ctk_image_about_us = ctk.CTkImage(pil_image_about_us, size=(30, 30))
    feedback_button = ctk.CTkButton(
        root,
        command=lambda: webbrowser.open("https://github.com/PLauncher-Team/PLauncher/issues"),
        width=int(language_manager.get("main.width_buttons")),
        image=ctk_image_about_us,
        text=language_manager.get("main.buttons.feedback"),
        font=("Segoe UI", 15, "bold"),
    )
    feedback_button.place(relx=0.02, rely=0.403, relwidth=int(language_manager.get("main.width_buttons")) / 1000, relheight=0.067)
    pywinstyles.set_opacity(feedback_button, color="#242424", value=0.8)
    if not LauncherConfig.IS_INTERNET:
        feedback_button.configure(state="disabled")
    
    pil_image_logs = PIL.Image.open("png/GUI/logs.png")
    ctk_image_logs = ctk.CTkImage(pil_image_logs, size=(30, 30))
    logs_button = ctk.CTkButton(
        root,
        text=language_manager.get("main.buttons.logs"),
        image=ctk_image_logs,
        font=("Segoe UI", 15, "bold"),
        command=open_logs,
    )
    logs_button.place(relx=0.02, rely=0.51, relwidth=int(language_manager.get("main.width_buttons")) / 1000, relheight=0.067)
    pywinstyles.set_opacity(logs_button, color="#242424", value=0.8)
    
    pil_image_instances = PIL.Image.open("png/GUI/instances.png")
    ctk_image_instances = ctk.CTkImage(pil_image_instances, size=(30, 30))
    mods_button = ctk.CTkButton(root, text=language_manager.get("main.buttons.mods"), image=ctk_image_instances, font=("Segoe UI", 15, "bold"), command=mod_viewer_window.deiconify)
    mods_button.place(relx=0.02, rely=0.617, relwidth=int(language_manager.get("main.width_buttons")) / 1000, relheight=0.067)
    pywinstyles.set_opacity(mods_button, color="#242424", value=0.8)
    
    pil_image_settings = PIL.Image.open("png/GUI/settings.png")
    ctk_image_settings = ctk.CTkImage(pil_image_settings, size=(30, 30))
    settings_button = ctk.CTkButton(
        root,
        text=language_manager.get("main.buttons.settings"),
        font=("Segoe UI", 15, "bold"),
        command=lambda: settings_controller.open_settings(),
        image=ctk_image_settings,
    )
    settings_button.place(relx=0.02, rely=0.724, relwidth=int(language_manager.get("main.width_buttons")) / 1000, relheight=0.067)
    pywinstyles.set_opacity(settings_button, color="#242424", value=0.8)
    
    version_combobox_ctk = ctk.CTkComboBox(
        root,
        state="readonly",
        font=("Segoe UI", 20),
        height=562 * 0.124
    )
    version_combobox_ctk.place(relx=0.343, rely=0.848, relwidth=0.313)
    pywinstyles.set_opacity(version_combobox_ctk, color="#242424", value=0.9)
    
    version_combobox = CTkScrollableDropdown(
        version_combobox_ctk,
        values=[],
        justify="left",
        command=set_version,
        font=("Segoe UI", 12),
        scrollbar_button_color=GuiOptions.fg_color,
        scrollbar_button_hover_color=GuiOptions.hover_color,
        groups=[
            ["Forge",    r"(?i)(?<!neo)forge.*"],
            ["Fabric",   r"(?i).*fabric-loader.*"],
            ["OptiFine", r"(?i).*optifine.*"],
            ["NeoForge", r"(?i).*neoforge.*"],
            ["Quilt",    r"(?i).*quilt.*"],
            ["Cleanroom", r"(?i).*cleanroom.*"],
            ["Minecraft", "__OTHERS__"],
            [language_manager.get("main.types_versions.installed").replace("(", "").replace(")", ""), rf"{re.escape(language_manager.get('main.types_versions.installed'))}\s*$"],
            [language_manager.get("main.types_versions.not_completed").replace("(", "").replace(")", ""), rf"{re.escape(language_manager.get('main.types_versions.not_completed'))}\s*$"]
        ],
        fps=LauncherConfig.FPS
    )
    version_combobox.search_entry.configure(font=("Segoe UI", 23))
    version_combobox.button_container.configure(border_width=0)
    version_combobox.pagination_frame.configure(border_width=0)
    
    launch_button = ctk.CTkButton(
        root,
        text=language_manager.get("main.buttons.launch_game"),
        command=lambda: threading.Thread(target=launch_game).start(),
        font=("Segoe UI", 20, "bold"),
    )
    launch_button.place(relx=0.671, rely=0.848, relwidth=0.313, relheight=0.124)
    pywinstyles.set_opacity(launch_button, color="#242424", value=0.9)
    
    loader_controller = LoaderController(
        online=LauncherConfig.IS_INTERNET,
        catalog=loader_catalog,
        installer=loader_installer,
        version_selector=choice_version_ctk,
        version_dropdown=choice_version,
        loader_selector=choice_loader,
        progress_bar=progress_loader,
        install_button=install_loader,
        launch_button=launch_button,
        settings_frame=content_frames[tabs[3]],
        language_manager=language_manager,
        logger=log,
        notify_error=show_error_notification,
        set_maximum=set_max_value,
        update_progress=progress_bar_update,
        reload_versions=load_versions,
        current_process=lambda: LaunchOptions.loader_process,
        kill_thread=kill_thread,
    )
    
    pywinstyles.change_header_color(root, GuiOptions.fg_color)
    
    blackout_frame.lift()
    settings_frame.lift()
    
    log(f"Инициализация лаунчера завершена за {time.perf_counter() - start_time:.2f} s")
    
    if not LauncherConfig.IS_INTERNET:
        ToastNotification(title=language_manager.get("messages.titles.warning"),
                    message=language_manager.get("messages.texts.warning.no_internet"),
                    toast_type="warning",
                    master=root)
        for c in (release_checkbox, snapshot_checkbox, old_alpha_check, old_beta_check, skins_ely_by_checkbox,
                  install_loader):
            c.configure(state="disabled")
    created = {name: value for name, value in locals().items() if not name.startswith("_")}
    globals().update(created)
    ui_support.configure(**created)
    return created
