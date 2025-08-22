ctk.set_appearance_mode("Dark")
if config["custom_theme"]:
    theme_path = config["custom_theme"]
else:
    themes = []
    for filename in os.listdir("themes"):
        full_path = os.path.join("themes", filename)
        if os.path.isfile(full_path):
            name_without_ext = os.path.splitext(filename)[0]
            themes.append(name_without_ext)
    theme_path = random.choice(themes)
log(f"Launcher theme: {theme_path}", source="gui")
ctk.set_default_color_theme(f"themes/{theme_path}.json")

root = ctk.CTk(fg_color="#242424")

screen_width = max(960, root.winfo_screenwidth())
screen_height = max(540, root.winfo_screenheight())
root_x = int(round(screen_width * 0.52083))
root_y = int(round(screen_height * 0.52037))
width_factor = root_x / 1000
height_factor = root_y / 562
settings_x = int(round(405 * width_factor))
settings_y = int(round(393 * height_factor))
crash_x = int(round(600 * width_factor))
crash_y = int(round(700 * height_factor))
feedback_x = int(round(500 * width_factor))
feedback_y = int(round(400 * height_factor))
scale = ((screen_width / 1920) + (screen_height / 1080)) / 2
fg_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"][1]
hover_color = ctk.ThemeManager.theme["CTkButton"]["hover_color"][1]
text_color = ctk.ThemeManager.theme["CTkButton"]["text_color"][1]

root.resizable(False, False)
root.geometry(f"{root_x}x{root_y}+{center(root, root_x, root_y)}")
root.protocol("WM_DELETE_WINDOW", ex)
root.title("PLauncher")

if not config["random_theme"]:
    selected_theme = config["selected_theme"]
else:
    selected_theme = random.randint(1, 5)
color_selected = selected_theme - 1

if config["custom_image"]:
    image_path = config["custom_image"]
else:
    image_path = os.path.join("png", "dark", f"{selected_theme}.png")

log(f"Launcher image: {image_path}", source="gui")

msg = None
pil_image = PIL.Image.open(image_path)
ctk_image = ctk.CTkImage(pil_image, size=(root_x, root_y))
label = ctk.CTkLabel(root, image=ctk_image)
label.place(relheight=1, relwidth=1)

crash_window = CrashLogWindow()

release_var = ctk.BooleanVar(value=config["release"])
snapshot_var = ctk.BooleanVar(value=config["snapshot"])
old_beta_var = ctk.BooleanVar(value=config["old_beta"])
old_alpha_var = ctk.BooleanVar(value=config["old_alpha"])
default_var = ctk.BooleanVar(value=config["default_path"])
hide_var = ctk.BooleanVar(value=config["hide"])
debug_var = ctk.BooleanVar(value=config["debug"])
check_var = ctk.BooleanVar(value=config["check_files"])
ely_by_var = ctk.BooleanVar(value=config["ely_by"])
default_skin_var = ctk.BooleanVar(value=config["default_skin"])
latest_version = version["version"]

version_frame = VersionFrame(root)
version_frame.place(relwidth=0.175, relheight=0.177, relx=0.797, rely=0.05)
blackout_frame = ctk.CTkFrame(root, fg_color="black")
blackout_frame.place(relwidth=1, relheight=1)
set_opacity(blackout_frame, value=0)
blackout_frame.bind("<Button-1>", lambda a: close_settings())

settings_frame = ctk.CTkFrame(root, fg_color="#252526")
settings_frame.place(relwidth=0.45, relheight=1, relx=1)
set_opacity(settings_frame, value=0.95)

header_frame = ctk.CTkFrame(settings_frame, fg_color="#252526")
header_frame.place(relx=0, rely=0, relwidth=1, relheight=0.1)
back_btn = ctk.CTkButton(
    header_frame,
    text="<",
    command=close_settings,
    font=get_dynamic_font("Segoe UI", 13)
)
back_btn.place(relx=0.02, rely=0.5, relwidth=0.066, relheight=0.533, anchor="w")

title_label = ctk.CTkLabel(
    header_frame,
    text=language_manager.get("settings.title"),
    font=get_dynamic_font("Segoe UI", 23, "bold")
)
title_label.place(relx=0.1, rely=0.5, anchor="w")

button_frame = ctk.CTkFrame(settings_frame)
button_frame.place(relx=0, rely=0.1, relwidth=1, relheight=0.1)

tabs = language_manager.get("settings.pages")
tab_buttons = {}
for i, name in enumerate(tabs):
    btn = ctk.CTkButton(
        button_frame,
        text=name,
        border_width=0,
        corner_radius=0,
        command=lambda n=name: show_tab(n),
        font=get_dynamic_font("Segoe UI", 13)
    )
    btn.place(relx=i*(1/len(tabs)), rely=0, relwidth=1/len(tabs), relheight=1)
    tab_buttons[name] = btn

indicator = ctk.CTkFrame(button_frame, fg_color="red", height=3)
indicator.place(relx=0, rely=1, anchor='sw', relwidth=1/len(tabs))
tab_buttons[tabs[4]].configure(state="disabled")
content_frames = {}
for name in tabs:
    frame = ctk.CTkFrame(settings_frame, fg_color="#252526")
    content_frames[name] = frame

ctk.CTkLabel(
    content_frames[tabs[0]],
    text=language_manager.get("settings.1_page.version_types_1"),
    font=get_dynamic_font("Segoe UI", 15, "bold")
).place(relwidth=1)

ctk.CTkLabel(
    content_frames[tabs[0]],
    text=language_manager.get("settings.1_page.version_types_2"),
    font=get_dynamic_font("Segoe UI", 12, "bold"),
    anchor="w",
).place(relwidth=1, rely=0.063)

release_checkbox = ctk.CTkCheckBox(
    content_frames[tabs[0]],
    factor=scale,
    text=language_manager.get("settings.1_page.release"),
    variable=release_var,
    command=save_versions_var,
    font=get_dynamic_font("Segoe UI", 13)
)
release_checkbox.place(rely=0.124)

snapshot_checkbox = ctk.CTkCheckBox(
    content_frames[tabs[0]],
    factor=scale,
    text=language_manager.get("settings.1_page.snapshots"),
    variable=snapshot_var,
    command=save_versions_var,
    font=get_dynamic_font("Segoe UI", 13)
)
snapshot_checkbox.place(relx=0.572, rely=0.124)

old_beta_check = ctk.CTkCheckBox(
    content_frames[tabs[0]],
    factor=scale,
    text=language_manager.get("settings.1_page.old_beta"),
    variable=old_beta_var,
    command=save_versions_var,
    font=get_dynamic_font("Segoe UI", 13)
)
old_beta_check.place(rely=0.19)

old_alpha_check = ctk.CTkCheckBox(
    content_frames[tabs[0]],
    factor=scale,
    text=language_manager.get("settings.1_page.old_alpha"),
    variable=old_alpha_var,
    command=save_versions_var,
    font=get_dynamic_font("Segoe UI", 13)
)
old_alpha_check.place(relx=0.572, rely=0.19)

ctk.CTkLabel(
    content_frames[tabs[0]],
    text=language_manager.get("settings.1_page.installed_versions"),
    font=get_dynamic_font("Segoe UI", 15, "bold"),
).place(relwidth=1, rely=0.331)
ctk.CTkLabel(
    content_frames[tabs[0]],
    text=language_manager.get("settings.1_page.manager_versions"),
    font=get_dynamic_font("Segoe UI", 12, "bold"),
    anchor="w",
).place(relwidth=1, rely=0.392)

installed_versions_combobox_ctk = ctk.CTkComboBox(
    content_frames[tabs[0]],
    border_width=0,
    state="readonly",
    font=get_dynamic_font("Segoe UI", 13),
    height=0.083 * settings_y
)
installed_versions_combobox_ctk.place(relwidth=0.92, rely=0.453)

installed_versions_combobox = CTkScrollableDropdown(
    installed_versions_combobox_ctk,
    values=[],
    justify="left",
    scrollbar_button_color=fg_color,
    scrollbar_button_hover_color=hover_color,
    pagination=False,
    font=get_dynamic_font("Segoe UI", 13),
)

del_version = ctk.CTkButton(
    content_frames[tabs[0]],
    text="-",
    command=del_installed_version,
    hover_color="red",
    font=get_dynamic_font("Segoe UI", 13)
)
del_version.place(relwidth=0.079, relheight=0.081, relx=0.921, rely=0.453)

ctk.CTkLabel(
    content_frames[tabs[0]],
    text=language_manager.get("settings.1_page.other_settings"),
    font=("Segoe UI", 15, "bold"),
).place(relwidth=1, relheight=0.087, rely=0.623)

texts_language = {
    "ru": "Русский",
    "uk": "Українська",
    "be": "Беларуский",
    "en": "English",
    "es": "Español"
}

texts_language_reverse = {
    "Русский": "ru",
    "Українська": "uk",
    "Беларуский": "be",
    "English": "en",
    "Español": "es"
}
language_choice = ctk.CTkSegmentedButton(content_frames[tabs[0]],
                                         values=list(texts_language.values()),
                                         command=select_language,
                                         font=get_dynamic_font("Segoe UI", 13))
language_choice.place(relwidth=1, relheight=0.087, rely=0.714)
language_choice.set(texts_language[language_manager.language])

check_files = ctk.CTkCheckBox(
    content_frames[tabs[0]],
    factor=scale,
    text=language_manager.get("settings.1_page.check_files"),
    command=lambda: save_set("check_files", check_var.get()),
    variable=check_var,
    font=get_dynamic_font("Segoe UI", 13)
)
check_files.place(rely=0.818)

debug_checkbox = ctk.CTkCheckBox(
    content_frames[tabs[0]],
    factor=scale,
    text=language_manager.get("settings.1_page.debug_mode"),
    command=lambda: save_set("debug", debug_var.get()),
    variable=debug_var,
    font=get_dynamic_font("Segoe UI", 13)
)
debug_checkbox.place(relx=0.55, rely=0.818)

hide_checkbox = ctk.CTkCheckBox(
    content_frames[tabs[0]],
    factor=scale,
    text=language_manager.get("settings.1_page.hide_launcher"),
    variable=hide_var,
    command=lambda: save_set("hide", hide_var.get()),
    font=get_dynamic_font("Segoe UI", 13)
)
hide_checkbox.place(rely=0.92)

ctk.CTkLabel(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.java_settings"),
    font=get_dynamic_font("Segoe UI", 15, "bold"),
).place(relwidth=1)

ctk.CTkLabel(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.java_used"),
    font=get_dynamic_font("Segoe UI", 12, "bold"),
    anchor="w",
).place(relwidth=1, rely=0.063)

java_combobox = ctk.CTkComboBox(
    content_frames[tabs[1]],
    values=[language_manager.get("settings.2_page.recommended_java")] + list(config["java_paths"].keys()) + [language_manager.get("settings.2_page.add")],
    border_width=0,
    state="readonly",
    command=on_select_java,
    font=get_dynamic_font("Segoe UI", 13),
    height=0.083 * settings_y
)
java_combobox.place(relwidth=0.92, rely=0.124)
if not config["java"]:
    java_combobox.set(language_manager.get("settings.2_page.recommended_java"))
else:
    java_combobox.set(config["java"])

del_java_button = ctk.CTkButton(
    content_frames[tabs[1]],
    text="-",
    command=del_java,
    hover_color="red",
    font=get_dynamic_font("Segoe UI", 13)
)
del_java_button.place(relwidth=0.079, relheight=0.081, relx=0.921, rely=0.124)

ctk.CTkLabel(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.amt_memory"),
    font=get_dynamic_font("Segoe UI", 12, "bold"),
    anchor="w",
).place(relwidth=1, rely=0.207)

memory_options = create_memory_options()
selected_memory = ctk.StringVar(root)
selected_memory.set(config["memory_args"])
previous_value = config["memory_args"]
memory_combobox = ctk.CTkComboBox(
    content_frames[tabs[1]],
    variable=selected_memory,
    values=memory_options,
    command=lambda h: on_select(),
    border_width=0,
    font=get_dynamic_font("Segoe UI", 13),
    height=0.083 * settings_y
)
memory_combobox.bind("<KeyRelease>", correct_value)
memory_combobox.bind("<Key>", correct_value)
memory_combobox.place(relwidth=1, rely=0.268)

ctk.CTkLabel(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.args_JVM"),
    font=get_dynamic_font("Segoe UI", 12, "bold"),
    anchor="w",
).place(relwidth=1, rely=0.351)

args_entry = ctk.CTkEntry(
    content_frames[tabs[1]],
    border_width=0,
    font=get_dynamic_font("Segoe UI", 13),
)
args_entry.insert(0, config["custom_args"])
args_entry.bind("<KeyRelease>", lambda h: entry_input())
args_entry.place(relwidth=1, relheight=0.083, rely=0.412)

ctk.CTkLabel(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.game_directory"),
    font=get_dynamic_font("Segoe UI", 15, "bold"),
).place(relwidth=1, rely=0.595)

default_directory = ctk.CTkCheckBox(
    content_frames[tabs[1]],
    factor=scale,
    text=language_manager.get("settings.2_page.default_path"),
    variable=default_var,
    font=get_dynamic_font("Segoe UI", 13)
)
default_directory.configure(
    command=lambda: change_mine(False)
)
default_directory.place(rely=0.658)

current_folder = ctk.CTkLabel(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.current_path") + minecraft_path,
    font=get_dynamic_font("Segoe UI", 12),
)
current_folder.place(relwidth=1, rely=0.9)

open_folder = ctk.CTkButton(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.open_folder"),
    font=get_dynamic_font("Segoe UI", 20, "bold"),
    command=lambda: os.startfile(minecraft_path),
)
open_folder.place(relwidth=0.79, relheight=0.15, rely=0.734)

change_folder = ctk.CTkButton(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.change_folder"),
    font=get_dynamic_font("Segoe UI", 13, "bold"),
)
if config["default_path"]:
    change_folder.configure(state="disabled")
change_folder.place(relwidth=0.205, relheight=0.15, relx=0.795, rely=0.734)
change_folder.configure(
    command=change_mine
)

frame_skin = ctk.CTkFrame(content_frames[tabs[2]], fg_color="transparent")
frame_skin.place(relwidth=1, relheight=0.6)
frame_skin.update_idletasks()
label_skin = ctk.CTkLabel(frame_skin)
label_skin.place(relheight=1, relx=0.5, rely=0.5, anchor="center")

update_skin_button = ctk.CTkButton(
    frame_skin,
    text=language_manager.get("settings.3_page.update"),
    font=get_dynamic_font("Segoe UI", 20),
    command=lambda: threading.Thread(target=set_skin).start(),
)
update_skin_button.place(relx=1, rely=1, relwidth=0.4, relheight=0.15, anchor="se")
set_opacity(update_skin_button, color="#242424")

select_skin_button = ctk.CTkButton(
    content_frames[tabs[2]],
    text=language_manager.get("settings.3_page.select_file_skin"),
    font=get_dynamic_font("Segoe UI", 20, "bold"),
    command=select_png_file,
)
select_skin_button.place(rely=0.61, relheight=0.15, relwidth=1)

skins_ely_by_checkbox = ctk.CTkCheckBox(
    content_frames[tabs[2]],
    factor=scale,
    text=language_manager.get("settings.3_page.use_ely_by"),
    command=lambda: [save_set("ely_by", ely_by_var.get()), update_controls(), threading.Thread(target=set_skin).start()],
    variable=ely_by_var,
    font=get_dynamic_font("Segoe UI", 13),
)
skins_ely_by_checkbox.place(rely=0.78)

skins_default_checkbox = ctk.CTkCheckBox(
    content_frames[tabs[2]],
    factor=scale,
    text=language_manager.get("settings.3_page.use_default_skin"),
    command=lambda: [save_set("default_skin", default_skin_var.get()), update_controls(), threading.Thread(target=set_skin).start()],
    variable=default_skin_var,
    font=get_dynamic_font("Segoe UI", 13),
)
skins_default_checkbox.place(rely=0.875)

update_controls()

dictionary_neoforge = {}
forge_versions_mine = []
neoforge_versions_mine = []
fabric_versions_mine = []
quilt_versions_mine = []
optifine_version_mine = []
loaders_versions_mine = {
    "Fabric": fabric_versions_mine,
    "Forge": forge_versions_mine,
    "Quilt": quilt_versions_mine,
    "OptiFine": optifine_version_mine,
    "NeoForge": neoforge_versions_mine,
}

chapter5 = ctk.CTkLabel(
    content_frames[tabs[3]],
    text=language_manager.get("settings.4_page.loaders_mods"),
    font=get_dynamic_font("Segoe UI", 15, "bold"),
)
chapter5.place(relwidth=1, relheight=0.086)

choice_version_ctk = ctk.CTkComboBox(
    content_frames[tabs[3]],
    state="readonly",
    border_width=0,
    font=get_dynamic_font("Segoe UI", 13),
    height=settings_y * 0.083
)
choice_version_ctk.place(relwidth=0.727, rely=0.099)
choice_version = CTkScrollableDropdown(
    choice_version_ctk,
    values=[],
    justify="left",
    scrollbar_button_color=fg_color,
    scrollbar_button_hover_color=hover_color,
    height=root_y,
)
choice_version.search_entry.configure(corner_radius=20, border_width=0, 
                                      font=get_dynamic_font("Segoe UI", 13),)

choice_loader = ctk.CTkComboBox(
    content_frames[tabs[3]],
    state="readonly",
    command=lambda y: choice_version.configure(values=list_ver(y)),
    border_width=0,
    values=[],
    font=get_dynamic_font("Segoe UI", 13),
    height=settings_y * 0.083
)
choice_loader.place(relwidth=0.272, relx=0.727, rely=0.099)

progress_loader = ctk.CTkProgressBar(
    content_frames[tabs[3]],
)
progress_loader.place(relwidth=1, relheight=0.087, rely=0.19)
progress_loader.set(0)

install_loader = ctk.CTkButton(
    content_frames[tabs[3]],
    text=language_manager.get("settings.4_page.install_loader"),
    font=get_dynamic_font("Segoe UI", 20, "bold"),
    command=lambda: threading.Thread(target=fun_install_loaders).start(),
)
install_loader.place(relwidth=1, relheight=0.206, rely=0.285)

threading.Thread(target=get_loaders_versions).start()

chapter4 = ctk.CTkLabel(
    content_frames[tabs[3]],
    text=language_manager.get("settings.4_page.mods_profiles"),
    font=get_dynamic_font("Segoe UI", 15, "bold"),
)
chapter4.place(relwidth=1, rely=0.543)

list_profiles = ctk.CTkComboBox(
    content_frames[tabs[3]],
    state="readonly",
    values=list_dir(),
    command=profile_select,
    font=get_dynamic_font("Segoe UI", 13),
    border_width=0,
    height=settings_y * 0.083
)
if not version["profile"]:
    list_profiles.set(language_manager.get("settings.4_page.no"))
else:
    list_profiles.set(version["profile"])
list_profiles.place(relwidth=1, rely=0.626)

add_profile_Entry = ctk.CTkEntry(
    content_frames[tabs[3]],
    border_width=0,
    font=get_dynamic_font("Segoe UI", 13),
)
add_profile_Entry.place(relwidth=1, relheight=0.083, rely=0.626)

add_profile_button = ctk.CTkButton(
    content_frames[tabs[3]],
    text=language_manager.get("settings.4_page.add"),
    command=fun_add_profile,
    hover_color="green",
    font=get_dynamic_font("Segoe UI", 13),
)
add_profile_button.place(relwidth=0.333, relheight=0.083, rely=0.71)

del_profile_button = ctk.CTkButton(
    content_frames[tabs[3]],
    text=language_manager.get("settings.4_page.delete"),
    command=del_profile,
    hover_color="red",
    font=get_dynamic_font("Segoe UI", 13),
)
del_profile_button.place(relwidth=0.333, relheight=0.083, relx=0.333, rely=0.71)

rename_profile_button = ctk.CTkButton(
    content_frames[tabs[3]],
    text=language_manager.get("settings.4_page.change"),
    command=fun_rename_profile,
    font=get_dynamic_font("Segoe UI", 13),
)
rename_profile_button.place(relwidth=0.333, relheight=0.083, relx=0.666, rely=0.71)

open_profile = ctk.CTkButton(
    content_frames[tabs[3]],
    text=language_manager.get("settings.4_page.open_folder"),
    font=get_dynamic_font("Segoe UI", 20, "bold"),
    command=open_folder_profile,
)
open_profile.place(relwidth=1, relheight=0.206, rely=0.793)
list_profiles.lift()

ctk.CTkLabel(
    content_frames[tabs[4]],
    text="Экспериментальные функции",
    font=get_dynamic_font("Segoe UI", 15, "bold")
).place(relwidth=1)

ctk.CTkLabel(
    content_frames[tabs[4]],
    text="Утилиты очистки и удаления данных",
    font=get_dynamic_font("Segoe UI", 15, "bold")
).place(relwidth=1, rely=0.697)

btn_clear_cache = ctk.CTkButton(
    content_frames[tabs[4]],
    text="Очистить кеш лаунчера",
    font=get_dynamic_font("Segoe UI", 13),
)
btn_clear_cache.place(relwidth=0.45, relheight=0.083, rely=0.797)

btn_reset_settings = ctk.CTkButton(
    content_frames[tabs[4]],
    text="Сбросить настройки",
    hover_color="red",
)
btn_reset_settings.place(relwidth=0.45, relheight=0.083, rely=0.917)

btn_delete_mc = ctk.CTkButton(
    content_frames[tabs[4]],
    text="Удалить данные Minecraft",
    hover_color="red",
)
btn_delete_mc.place(relwidth=0.45, relheight=0.083, relx=0.55, rely=0.797)

btn_uninstall = ctk.CTkButton(
    content_frames[tabs[4]],
    text="Удалить лаунчер",
    hover_color="red",
)
btn_uninstall.place(relwidth=0.45, relheight=0.083, relx=0.55, rely=0.917)

status_label = ctk.CTkLabel(
    root,
    text=language_manager.get("main.status.waiting"),
    font=get_dynamic_font("Segoe UI", 17, "bold"),
    anchor="s",
    fg_color="#242424",
    bg_color="#242424"
)
status_label.place(relx=0.671, rely=0.725, relwidth=0.313, relheight=0.074)
set_opacity(status_label, color="#242424")

progress_bar = ctk.CTkProgressBar(
    root,
)
progress_bar.place(relx=0.675, rely=0.807, relwidth=0.305, relheight=0.021)
progress_bar.set(0)
set_opacity(progress_bar, value=0.9)

username_entry = ctk.CTkEntry(
    root,
    placeholder_text="Steve",
    font=get_dynamic_font("Segoe UI", 23),
    border_width=0,
)
username_entry.bind("<KeyRelease>", lambda h: save_config_menu())
username_entry.insert(0, config["name"])
username_entry.place(relx=0.015, rely=0.848, relwidth=0.313, relheight=0.124)
set_opacity(username_entry, color="#242424", value=0.9)

pil_image_about_us = PIL.Image.open("png/GUI/feedback.png")
ctk_image_about_us = ctk.CTkImage(pil_image_about_us, size=(int(30 * width_factor), int(30 * height_factor)))
feedback_button = ctk.CTkButton(
    root,
    width=language_manager.get("main.width_buttons"),
    command=FeedbackApp,  
    image=ctk_image_about_us,
    text=language_manager.get("main.buttons.feedback"),
    font=get_dynamic_font("Segoe UI", 15, "bold"),
)
feedback_button.place(relx=0.02, rely=0.51, relwidth=language_manager.get("main.width_buttons") * width_factor / root_x, relheight=0.067)
set_opacity(feedback_button, color="#242424", value=0.8)
if not IS_INTERNET:
    feedback_button.configure(state="disabled")

pil_image_logs = PIL.Image.open("png/GUI/logs.png")
ctk_image_logs = ctk.CTkImage(pil_image_logs, size=(int(30 * width_factor), int(30 * height_factor)))
logs_button = ctk.CTkButton(
    root,
    text=language_manager.get("main.buttons.logs"),
    image=ctk_image_logs,
    font=get_dynamic_font("Segoe UI", 15, "bold"),
    command=open_logs,
)
logs_button.place(relx=0.02, rely=0.617, relwidth=language_manager.get("main.width_buttons") * width_factor / root_x, relheight=0.067)
set_opacity(logs_button, color="#242424", value=0.8)

pil_image_settings = PIL.Image.open("png/GUI/settings.png")
ctk_image_settings = ctk.CTkImage(pil_image_settings, size=(int(30 * width_factor), int(30 * height_factor)))
settings_button = ctk.CTkButton(
    root,
    text=language_manager.get("main.buttons.settings"),
    font=get_dynamic_font("Segoe UI", 15, "bold"),
    command=open_settings,
    image=ctk_image_settings,
)
settings_button.place(relx=0.02, rely=0.724, relwidth=language_manager.get("main.width_buttons") * width_factor / root_x, relheight=0.067)
set_opacity(settings_button, color="#242424", value=0.8)

version_combobox_ctk = ctk.CTkComboBox(
    root,
    state="readonly",
    font=get_dynamic_font("Segoe UI", 20),
    border_width=0,
    height=root_y * 0.124
)
version_combobox_ctk.set(version["version"])
version_combobox_ctk.place(relx=0.343, rely=0.848, relwidth=0.313)
set_opacity(version_combobox_ctk, color="#242424", value=0.9)

installed_text = language_manager.get("main.types_versions.installed")
not_complete_text = language_manager.get("main.types_versions.not_completed")
version_combobox = CTkScrollableDropdown(
    version_combobox_ctk,
    values=[],
    justify="left",
    command=set_version,
    font=get_dynamic_font("Segoe UI", 12),
    scrollbar_button_color=fg_color,
    scrollbar_button_hover_color=hover_color,
    groups=[
        ["Forge",    r"(?i)(?<!neo)forge.*"],
        ["Fabric",   r"(?i).*fabric-loader.*"],
        ["OptiFine", r"(?i).*optifine.*"],
        ["NeoForge", r"(?i).*neoforge.*"],
        ["Quilt",    r"(?i).*quilt.*"],
        ["Minecraft", "__OTHERS__"],
        [installed_text.replace("(", "").replace(")", ""), rf"{re.escape(installed_text)}\s*$"],
        [not_complete_text.replace("(", "").replace(")", ""), rf"{re.escape(not_complete_text)}\s*$"]
    ],
    fps=FPS
)
version_combobox.search_entry.configure(font=get_dynamic_font("Segoe UI", 23),
                                        border_width=0)

launch_button = ctk.CTkButton(
    root,
    text=language_manager.get("main.buttons.launch_game"),
    command=lambda: threading.Thread(target=launch_game).start(),
    font=get_dynamic_font("Segoe UI", 20, "bold"),
)
launch_button.place(relx=0.671, rely=0.848, relwidth=0.313, relheight=0.124)
set_opacity(launch_button, color="#242424", value=0.9)

hPyT.title_bar_color.set(root, color_name_to_hex(hover_color))

root.after(0, thread_load_versions)

blackout_frame.lift()
settings_frame.lift()

root.bind("<Configure>", lambda event: relative_center(), add="+")

root.after(0, lambda: show_tab(tabs[0]))

log(f"Done! ({perf_counter() - start_time:.2f} s)", source="gui")

if not IS_INTERNET:
    new_message(title=language_manager.get("messages.titles.warning"),
                message=language_manager.get("messages.texts.warning.no_internet"),
                icon="warning", option_1=language_manager.get("messages.answers.ok"))
    for c in (release_checkbox, snapshot_checkbox, old_alpha_check, old_beta_check, skins_ely_by_checkbox,
              install_loader):
        c.configure(state="disabled")