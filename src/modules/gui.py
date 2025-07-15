import hPyT

root = ctk.CTk()

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

root.resizable(False, False)
root.geometry(f"{root_x}x{root_y}+{center(root, root_x, root_y)}")
root.protocol("WM_DELETE_WINDOW", ex)
root.title("PLauncher")

theme_type = "dark"
if not config["random_theme"]:
    selected_theme = config["selected_theme"]
else:
    selected_theme = randint(1, 5)
color_selected = selected_theme - 1

image_path = os.path.join("png", theme_type, f"{selected_theme}.png")

msg = None
pil_image = Image.open(image_path)
ctk_image = ctk.CTkImage(pil_image, size=(root_x, root_y))
label = ctk.CTkLabel(root, image=ctk_image)
label.place(relheight=1, relwidth=1)

dominant_color = ['#202029', '#15252e', '#14232c', '#111d24', "#19243f"][color_selected]
lighten_dominant_15 = ['#3d3d4e', '#244050', '#233d4d', '#1d323f', "#2b3e6c"][color_selected]
lighten_dominant_10 = ['#333342', '#1f3745', '#1e3442', '#192b36', "#25355d"][color_selected]
lighten_dominant_5 = ['#2a2a35', '#1a2e39', '#192b37', '#15242d', "#1f2d4e"][color_selected]
user_color = "white"

if config["custom_theme"]:
    theme_type = "light" if user_color == "black" else "dark"

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
    fg_color=lighten_dominant_10,
    hover_color=lighten_dominant_5,
    text_color=user_color,
    command=close_settings,
    font=get_dynamic_font("Segoe UI", 13)
)
back_btn.place(relx=0.02, rely=0.5, relwidth=0.066, relheight=0.533, anchor="w")

title_label = ctk.CTkLabel(
    header_frame,
    text=language_manager.get("settings.title"),
    font=get_dynamic_font("Segoe UI", 23, "bold"),
    text_color=user_color
)
title_label.place(relx=0.1, rely=0.5, anchor="w")

button_frame = ctk.CTkFrame(settings_frame, fg_color=lighten_dominant_10)
button_frame.place(relx=0, rely=0.1, relwidth=1, relheight=0.1)

tabs = language_manager.get("settings.pages")
tab_buttons = {}
for i, name in enumerate(tabs):
    btn = ctk.CTkButton(
        button_frame,
        text=name,
        corner_radius=0,
        border_width=0,
        hover_color=lighten_dominant_5,
        text_color="gray",
        command=lambda n=name: show_tab(n),
        font=get_dynamic_font("Segoe UI", 13)
    )
    btn.place(relx=i*(1/len(tabs)), rely=0, relwidth=1/len(tabs), relheight=1)
    tab_buttons[name] = btn

indicator = ctk.CTkFrame(button_frame, fg_color="red", height=3, corner_radius=0)
indicator.place(relx=0, rely=1, anchor='sw', relwidth=1/len(tabs))
tab_buttons[tabs[4]].configure(state="disabled")
content_frames = {}
for name in tabs:
    frame = ctk.CTkFrame(settings_frame, fg_color="#252526")
    content_frames[name] = frame

ctk.CTkLabel(
    content_frames[tabs[0]],
    text=language_manager.get("settings.1_page.version_types_1"),
    font=get_dynamic_font("Segoe UI", 15, "bold"),
    text_color=user_color
).place(relwidth=1)

ctk.CTkLabel(
    content_frames[tabs[0]],
    text=language_manager.get("settings.1_page.version_types_2"),
    font=get_dynamic_font("Segoe UI", 12, "bold"),
    anchor="w",
    text_color="gray",
).place(relwidth=1, rely=0.063)

release_checkbox = ctk.CTkCheckBox(
    content_frames[tabs[0]],
    factor=scale,
    text=language_manager.get("settings.1_page.release"),
    variable=release_var,
    command=save_versions_var,
    text_color=user_color,
    fg_color=lighten_dominant_15,
    hover_color=lighten_dominant_15,
    checkmark_color=user_color,
    font=get_dynamic_font("Segoe UI", 13)
)
release_checkbox.place(rely=0.124)

snapshot_checkbox = ctk.CTkCheckBox(
    content_frames[tabs[0]],
    factor=scale,
    text=language_manager.get("settings.1_page.snapshots"),
    variable=snapshot_var,
    command=save_versions_var,
    text_color=user_color,
    fg_color=lighten_dominant_15,
    hover_color=lighten_dominant_15,
    checkmark_color=user_color,
    font=get_dynamic_font("Segoe UI", 13)
)
snapshot_checkbox.place(relx=0.572, rely=0.124)

old_beta_check = ctk.CTkCheckBox(
    content_frames[tabs[0]],
    factor=scale,
    text=language_manager.get("settings.1_page.old_beta"),
    variable=old_beta_var,
    command=save_versions_var,
    text_color=user_color,
    fg_color=lighten_dominant_15,
    hover_color=lighten_dominant_15,
    checkmark_color=user_color,
    font=get_dynamic_font("Segoe UI", 13)
)
old_beta_check.place(rely=0.19)

old_alpha_check = ctk.CTkCheckBox(
    content_frames[tabs[0]],
    factor=scale,
    text=language_manager.get("settings.1_page.old_alpha"),
    variable=old_alpha_var,
    command=save_versions_var,
    text_color=user_color,
    fg_color=lighten_dominant_15,
    hover_color=lighten_dominant_15,
    checkmark_color=user_color,
    font=get_dynamic_font("Segoe UI", 13)
)
old_alpha_check.place(relx=0.572, rely=0.19)

ctk.CTkLabel(
    content_frames[tabs[0]],
    text=language_manager.get("settings.1_page.installed_versions"),
    font=get_dynamic_font("Segoe UI", 15, "bold"),
    text_color=user_color,
).place(relwidth=1, rely=0.331)
ctk.CTkLabel(
    content_frames[tabs[0]],
    text=language_manager.get("settings.1_page.manager_versions"),
    font=get_dynamic_font("Segoe UI", 12, "bold"),
    anchor="w",
    text_color="gray",
).place(relwidth=1, rely=0.392)

installed_versions_combobox_ctk = ctk.CTkComboBox(
    content_frames[tabs[0]],
    text_color=user_color,
    border_width=0,
    state="readonly",
    font=get_dynamic_font("Segoe UI", 13),
    fg_color=lighten_dominant_10,
    dropdown_hover_color=lighten_dominant_5,
    button_color=lighten_dominant_5,
    dropdown_fg_color=lighten_dominant_10,
    height=0.083 * settings_y
)
installed_versions_combobox_ctk.place(relwidth=0.92, rely=0.453)

installed_versions_combobox = CTkScrollableDropdown(
    installed_versions_combobox_ctk,
    values=[],
    justify="left",
    height=root_y,
    pagination=False,
    fg_color=lighten_dominant_5,
    button_color=lighten_dominant_10,
    hover_color=lighten_dominant_15,
    font=get_dynamic_font("Segoe UI", 13),
)

del_version = ctk.CTkButton(
    content_frames[tabs[0]],
    text="-",
    command=del_installed_version,
    fg_color=lighten_dominant_10,
    hover_color="red",
    text_color=user_color,
    font=get_dynamic_font("Segoe UI", 13)
)
del_version.place(relwidth=0.079, relheight=0.081, relx=0.921, rely=0.453)

ctk.CTkLabel(
    content_frames[tabs[0]],
    text=language_manager.get("settings.1_page.other_settings"),
    font=("Segoe UI", 15, "bold"),
    text_color=user_color,
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
                                         text_color=user_color,
                                         fg_color=dominant_color,
                                         selected_color=lighten_dominant_10,
                                         selected_hover_color=lighten_dominant_5,
                                         unselected_color=lighten_dominant_15,
                                         unselected_hover_color=lighten_dominant_10,
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
    text_color=user_color,
    fg_color=lighten_dominant_15,
    hover_color=lighten_dominant_15,
    checkmark_color=user_color,
    font=get_dynamic_font("Segoe UI", 13)
)
check_files.place(rely=0.818)

debug_checkbox = ctk.CTkCheckBox(
    content_frames[tabs[0]],
    factor=scale,
    text=language_manager.get("settings.1_page.debug_mode"),
    command=lambda: save_set("debug", debug_var.get()),
    variable=debug_var,
    text_color=user_color,
    fg_color=lighten_dominant_15,
    hover_color=lighten_dominant_15,
    checkmark_color=user_color,
    font=get_dynamic_font("Segoe UI", 13)
)
debug_checkbox.place(relx=0.55, rely=0.818)

hide_checkbox = ctk.CTkCheckBox(
    content_frames[tabs[0]],
    factor=scale,
    text=language_manager.get("settings.1_page.hide_launcher"),
    variable=hide_var,
    command=lambda: save_set("hide", hide_var.get()),
    text_color=user_color,
    fg_color=lighten_dominant_15,
    hover_color=lighten_dominant_15,
    checkmark_color=user_color,
    font=get_dynamic_font("Segoe UI", 13)
)
hide_checkbox.place(rely=0.92)

ctk.CTkLabel(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.java_settings"),
    font=get_dynamic_font("Segoe UI", 15, "bold"),
    text_color=user_color,
).place(relwidth=1)

ctk.CTkLabel(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.java_used"),
    font=get_dynamic_font("Segoe UI", 12, "bold"),
    anchor="w",
    text_color="gray",
).place(relwidth=1, rely=0.063)

java_combobox = ctk.CTkComboBox(
    content_frames[tabs[1]],
    values=[language_manager.get("settings.2_page.recommended_java")] + list(config["java_paths"].keys()) + [language_manager.get("settings.2_page.add")],
    text_color=user_color,
    border_width=0,
    state="readonly",
    command=on_select_java,
    font=get_dynamic_font("Segoe UI", 13),
    fg_color=lighten_dominant_10,
    dropdown_hover_color=lighten_dominant_5,
    button_color=lighten_dominant_5,
    dropdown_fg_color=lighten_dominant_10,
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
    fg_color=lighten_dominant_10,
    hover_color="red",
    text_color=user_color,
    font=get_dynamic_font("Segoe UI", 13)
)
del_java_button.place(relwidth=0.079, relheight=0.081, relx=0.921, rely=0.124)

ctk.CTkLabel(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.amt_memory"),
    font=get_dynamic_font("Segoe UI", 12, "bold"),
    anchor="w",
    text_color="gray",
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
    text_color=user_color,
    border_width=0,
    font=get_dynamic_font("Segoe UI", 13),
    fg_color=lighten_dominant_10,
    dropdown_hover_color=lighten_dominant_5,
    button_color=lighten_dominant_5,
    dropdown_fg_color=lighten_dominant_10,
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
    text_color="gray",
).place(relwidth=1, rely=0.351)

args_entry = ctk.CTkEntry(
    content_frames[tabs[1]], 
    text_color=user_color,
    border_width=0,
    fg_color=lighten_dominant_10,
    font=get_dynamic_font("Segoe UI", 13),
)
args_entry.insert(0, config["custom_args"])
args_entry.bind("<KeyRelease>", lambda h: entry_input())
args_entry.place(relwidth=1, relheight=0.083, rely=0.412)

ctk.CTkLabel(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.game_directory"),
    font=get_dynamic_font("Segoe UI", 15, "bold"),
    text_color=user_color,
).place(relwidth=1, rely=0.595)

default_directory = ctk.CTkCheckBox(
    content_frames[tabs[1]],
    factor=scale,
    text=language_manager.get("settings.2_page.default_path"),
    variable=default_var,
    text_color=user_color,
    fg_color=lighten_dominant_15,
    hover_color=lighten_dominant_15,
    checkmark_color=user_color,
    font=get_dynamic_font("Segoe UI", 13)
)
default_directory.configure(
    command=lambda: change_mine(False)
)
default_directory.place(rely=0.658)

current_folder = ctk.CTkLabel(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.current_path") + minecraft_path,
    text_color="gray",
    font=get_dynamic_font("Segoe UI", 12),
)
current_folder.place(relwidth=1, rely=0.9)

open_folder = ctk.CTkButton(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.open_folder"),
    font=get_dynamic_font("Segoe UI", 20, "bold"),
    fg_color=lighten_dominant_10,
    hover_color=lighten_dominant_5,
    command=lambda: os.startfile(minecraft_path),
    text_color=user_color,
)
open_folder.place(relwidth=0.79, relheight=0.15, rely=0.734)

change_folder = ctk.CTkButton(
    content_frames[tabs[1]],
    text=language_manager.get("settings.2_page.change_folder"),
    font=get_dynamic_font("Segoe UI", 13, "bold"),
    text_color=user_color,
    fg_color=lighten_dominant_10,
    hover_color=lighten_dominant_5,
)
if config["default_path"]:
    change_folder.configure(state="disabled")
change_folder.place(relwidth=0.205, relheight=0.15, relx=0.795, rely=0.734)
change_folder.configure(
    command=change_mine
)

frame_skin = ctk.CTkFrame(content_frames[tabs[2]], fg_color=dominant_color, corner_radius=20)
frame_skin.place(relwidth=1, relheight=0.6)
frame_skin.update_idletasks()
label_skin = ctk.CTkLabel(frame_skin)
label_skin.place(relheight=1, relx=0.5, rely=0.5, anchor="center")

update_skin_button = ctk.CTkButton(
    frame_skin,
    text=language_manager.get("settings.3_page.update"),
    bg_color="#000001",
    font=get_dynamic_font("Segoe UI", 20),
    command=lambda: threading.Thread(target=set_skin).start(),
    text_color=user_color,
    fg_color=lighten_dominant_10,
    hover_color=lighten_dominant_5, 
    corner_radius=20,
)
update_skin_button.place(relx=1, rely=1, relwidth=0.4, relheight=0.15, anchor="se")
set_opacity(update_skin_button, color="#000001")

select_skin_button = ctk.CTkButton(
    content_frames[tabs[2]],
    text=language_manager.get("settings.3_page.select_file_skin"),
    font=get_dynamic_font("Segoe UI", 20, "bold"),
    command=select_png_file,
    text_color=user_color,
    fg_color=lighten_dominant_10,
    hover_color=lighten_dominant_5,
)
select_skin_button.place(rely=0.61, relheight=0.15, relwidth=1)

skins_ely_by_checkbox = ctk.CTkCheckBox(
    content_frames[tabs[2]],
    factor=scale,
    text=language_manager.get("settings.3_page.use_ely_by"),
    command=lambda: [save_set("ely_by", ely_by_var.get()), update_controls(), threading.Thread(target=set_skin).start()],
    variable=ely_by_var,
    text_color=user_color,
    fg_color=lighten_dominant_15,
    hover_color=lighten_dominant_15,
    checkmark_color=user_color,
    font=get_dynamic_font("Segoe UI", 13),
)
skins_ely_by_checkbox.place(rely=0.78)

skins_default_checkbox = ctk.CTkCheckBox(
    content_frames[tabs[2]],
    factor=scale,
    text=language_manager.get("settings.3_page.use_default_skin"),
    command=lambda: [save_set("default_skin", default_skin_var.get()), update_controls(), threading.Thread(target=set_skin).start()],
    variable=default_skin_var,
    text_color=user_color,
    fg_color=lighten_dominant_15,
    hover_color=lighten_dominant_15,
    checkmark_color=user_color,
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
    text_color=user_color,
)
chapter5.place(relwidth=1, relheight=0.086)

choice_version_ctk = ctk.CTkComboBox(
    content_frames[tabs[3]],
    state="readonly",
    text_color=user_color,
    border_width=0,
    fg_color=lighten_dominant_10,
    dropdown_hover_color=lighten_dominant_5,
    button_color=lighten_dominant_5,
    dropdown_fg_color=lighten_dominant_10,
    font=get_dynamic_font("Segoe UI", 13),
    height=settings_y * 0.083
)
choice_version_ctk.place(relwidth=0.727, rely=0.099)
choice_version = CTkScrollableDropdown(
    choice_version_ctk,
    values=[],
    justify="left",
    height=root_y,
    fg_color=lighten_dominant_5,
    button_color=lighten_dominant_10,
    hover_color=lighten_dominant_15,
)
choice_version.search_entry.configure(text_color=user_color, corner_radius=20, border_width=0, fg_color=lighten_dominant_10, 
                                      font=get_dynamic_font("Segoe UI", 13),)

choice_loader = ctk.CTkComboBox(
    content_frames[tabs[3]],
    state="readonly",
    command=lambda y: choice_version.configure(values=list_ver(y)),
    text_color=user_color,
    border_width=0,
    values=[],
    font=get_dynamic_font("Segoe UI", 13),
    fg_color=lighten_dominant_10,
    dropdown_hover_color=lighten_dominant_5,
    button_color=lighten_dominant_5,
    dropdown_fg_color=lighten_dominant_10,
    height=settings_y * 0.083
)
choice_loader.place(relwidth=0.272, relx=0.727, rely=0.099)

progress_loader = ctk.CTkProgressBar(
    content_frames[tabs[3]],
    fg_color=lighten_dominant_5,
    progress_color=lighten_dominant_5,
)
progress_loader.set(0)
progress_loader.place(relwidth=1, relheight=0.087, rely=0.19)

install_loader = ctk.CTkButton(
    content_frames[tabs[3]],
    text=language_manager.get("settings.4_page.install_loader"),
    font=get_dynamic_font("Segoe UI", 20, "bold"),
    fg_color=lighten_dominant_10,
    hover_color=lighten_dominant_5,
    command=lambda: threading.Thread(target=fun_install_loaders).start(),
    text_color=user_color,
)
install_loader.place(relwidth=1, relheight=0.206, rely=0.285)

threading.Thread(target=get_loaders_versions).start()

chapter4 = ctk.CTkLabel(
    content_frames[tabs[3]],
    text=language_manager.get("settings.4_page.mods_profiles"),
    font=get_dynamic_font("Segoe UI", 15, "bold"),
    text_color=user_color,
)
chapter4.place(relwidth=1, rely=0.543)

list_profiles = ctk.CTkComboBox(
    content_frames[tabs[3]],
    state="readonly",
    values=list_dir(),
    command=profile_select,
    font=get_dynamic_font("Segoe UI", 13),
    text_color=user_color,
    border_width=0,
    fg_color=lighten_dominant_10,
    dropdown_hover_color=lighten_dominant_5,
    button_color=lighten_dominant_5,
    dropdown_fg_color=lighten_dominant_10,
    height=settings_y * 0.083
)
if not version["profile"]:
    list_profiles.set(language_manager.get("settings.4_page.no"))
else:
    list_profiles.set(version["profile"])
list_profiles.place(relwidth=1, rely=0.626)

add_profile_Entry = ctk.CTkEntry(
    content_frames[tabs[3]],
    text_color=user_color,
    border_width=0,
    fg_color=lighten_dominant_10,
    font=get_dynamic_font("Segoe UI", 13),
)
add_profile_Entry.place(relwidth=1, relheight=0.083, rely=0.626)

add_profile_button = ctk.CTkButton(
    content_frames[tabs[3]],
    text=language_manager.get("settings.4_page.add"),
    command=fun_add_profile,
    hover_color="green",
    text_color=user_color,
    fg_color=lighten_dominant_10,
    font=get_dynamic_font("Segoe UI", 13),
)
add_profile_button.place(relwidth=0.333, relheight=0.083, rely=0.71)

del_profile_button = ctk.CTkButton(
    content_frames[tabs[3]],
    text=language_manager.get("settings.4_page.delete"),
    command=del_profile,
    hover_color="red",
    text_color=user_color,
    fg_color=lighten_dominant_10,
    font=get_dynamic_font("Segoe UI", 13),
)
del_profile_button.place(relwidth=0.333, relheight=0.083, relx=0.333, rely=0.71)

rename_profile_button = ctk.CTkButton(
    content_frames[tabs[3]],
    text=language_manager.get("settings.4_page.change"),
    command=fun_rename_profile,
    text_color=user_color,
    fg_color=lighten_dominant_10,
    hover_color=lighten_dominant_5,
    font=get_dynamic_font("Segoe UI", 13),
)
rename_profile_button.place(relwidth=0.333, relheight=0.083, relx=0.666, rely=0.71)

open_profile = ctk.CTkButton(
    content_frames[tabs[3]],
    text=language_manager.get("settings.4_page.open_folder"),
    font=get_dynamic_font("Segoe UI", 20, "bold"),
    command=open_folder_profile,
    text_color=user_color,
    fg_color=lighten_dominant_10,
    hover_color=lighten_dominant_5,
)
open_profile.place(relwidth=1, relheight=0.206, rely=0.793)
list_profiles.lift()

ctk.CTkLabel(
    content_frames[tabs[4]],
    text="Экспериментальные функции",
    font=get_dynamic_font("Segoe UI", 15, "bold"),
    text_color=user_color
).place(relwidth=1)

ctk.CTkLabel(
    content_frames[tabs[4]],
    text="Утилиты очистки и удаления данных",
    font=get_dynamic_font("Segoe UI", 15, "bold"),
    text_color=user_color
).place(relwidth=1, rely=0.697)

btn_clear_cache = ctk.CTkButton(
    content_frames[tabs[4]],
    text="Очистить кеш лаунчера",
    font=get_dynamic_font("Segoe UI", 13),
    fg_color=lighten_dominant_10,
    hover_color=lighten_dominant_5,
    text_color=user_color,
)
btn_clear_cache.place(relwidth=0.45, relheight=0.083, rely=0.797)

btn_reset_settings = ctk.CTkButton(
    content_frames[tabs[4]],
    text="Сбросить настройки",
    fg_color=lighten_dominant_10,
    hover_color="red",
    text_color=user_color,
)
btn_reset_settings.place(relwidth=0.45, relheight=0.083, rely=0.917)

btn_delete_mc = ctk.CTkButton(
    content_frames[tabs[4]],
    text="Удалить данные Minecraft",
    fg_color=lighten_dominant_10,
    hover_color="red",
    text_color=user_color,
)
btn_delete_mc.place(relwidth=0.45, relheight=0.083, relx=0.55, rely=0.797)

btn_uninstall = ctk.CTkButton(
    content_frames[tabs[4]],
    text="Удалить лаунчер",
    fg_color=lighten_dominant_10,
    hover_color="red",
    text_color=user_color,
)
btn_uninstall.place(relwidth=0.45, relheight=0.083, relx=0.55, rely=0.917)

status_label = ctk.CTkLabel(
    root,
    text=language_manager.get("main.status.waiting"),
    font=get_dynamic_font("Segoe UI", 17, "bold"),
    anchor="s",
    text_color=user_color,
    image=snip_image(pil_image, 671 * width_factor, 408 * height_factor, 984 * width_factor, 450 * height_factor),
)
status_label.place(relx=0.671, rely=0.725, relwidth=0.313, relheight=0.074)
status_label.lower()
label.lower()

progress_bg = ctk.CTkProgressBar(
    root,
    corner_radius=20,
    bg_color="#000001",
    fg_color=lighten_dominant_10,
    progress_color=lighten_dominant_10,
)
progress_bg.place(relx=0.671, rely=0.8, relwidth=0.313, relheight=0.035)
set_opacity(progress_bg, color="#000001", value=0.9)

progress_bar = ctk.CTkProgressBar(
    root,
    corner_radius=20,
    bg_color=lighten_dominant_10,
    progress_color=lighten_dominant_5,
    fg_color=lighten_dominant_5,
)
progress_bar.place(relx=0.675, rely=0.807, relwidth=0.305, relheight=0.021)
set_opacity(progress_bar, value=0.9)

username_entry = ctk.CTkEntry(
    root,
    placeholder_text="Steve",
    font=get_dynamic_font("Segoe UI", 23),
    text_color=user_color,
    corner_radius=20,
    bg_color="#000001",
    border_width=0,
    fg_color=lighten_dominant_10
)
username_entry.bind("<KeyRelease>", lambda h: save_config_menu())
username_entry.insert(0, config["name"])
username_entry.place(relx=0.015, rely=0.848, relwidth=0.313, relheight=0.124)
set_opacity(username_entry, color="#000001", value=0.9)

pil_image_about_us = Image.open("png/GUI/feedback.png")
ctk_image_about_us = ctk.CTkImage(pil_image_about_us, size=(int(30 * width_factor), int(30 * height_factor)))
feedback_button = ctk.CTkButton(
    root,
    width=language_manager.get("main.width_buttons"),
    corner_radius=20,
    command=FeedbackApp,  
    bg_color="#000001",
    fg_color=lighten_dominant_10,
    image=ctk_image_about_us,
    text=language_manager.get("main.buttons.feedback"),
    text_color=user_color,
    font=get_dynamic_font("Segoe UI", 15, "bold"),
    hover_color=lighten_dominant_5,
)
feedback_button.place(relx=0.02, rely=0.51, relwidth=language_manager.get("main.width_buttons") * width_factor / root_x, relheight=0.067)
set_opacity(feedback_button, color="#000001", value=0.8)
if not IS_INTERNET:
    feedback_button.configure(state="disabled")

pil_image_logs = Image.open("png/GUI/logs.png")
ctk_image_logs = ctk.CTkImage(pil_image_logs, size=(int(30 * width_factor), int(30 * height_factor)))
logs_button = ctk.CTkButton(
    root,
    text=language_manager.get("main.buttons.logs"),
    image=ctk_image_logs,
    bg_color="#000001",
    corner_radius=20,
    fg_color=lighten_dominant_10,
    text_color=user_color,
    font=get_dynamic_font("Segoe UI", 15, "bold"),
    command=open_logs,
    hover_color=lighten_dominant_5,
)
logs_button.place(relx=0.02, rely=0.617, relwidth=language_manager.get("main.width_buttons") * width_factor / root_x, relheight=0.067)
set_opacity(logs_button, color="#000001", value=0.8)

pil_image_settings = Image.open("png/GUI/settings.png")
ctk_image_settings = ctk.CTkImage(pil_image_settings, size=(int(30 * width_factor), int(30 * height_factor)))
settings_button = ctk.CTkButton(
    root,
    text=language_manager.get("main.buttons.settings"),
    bg_color="#000001",
    corner_radius=20,
    fg_color=lighten_dominant_10,
    text_color=user_color,
    font=get_dynamic_font("Segoe UI", 15, "bold"),
    command=open_settings,
    hover_color=lighten_dominant_5,
    image=ctk_image_settings,
)
settings_button.place(relx=0.02, rely=0.724, relwidth=language_manager.get("main.width_buttons") * width_factor / root_x, relheight=0.067)
set_opacity(settings_button, color="#000001", value=0.8)

version_combobox_ctk = ctk.CTkComboBox(
    root,
    state="readonly",
    corner_radius=20,
    fg_color=lighten_dominant_10,
    dropdown_hover_color=lighten_dominant_5,
    font=get_dynamic_font("Segoe UI", 20),
    bg_color="#000001",
    border_width=0,
    button_color=lighten_dominant_5,
    dropdown_fg_color=lighten_dominant_5,
    text_color=user_color,
    height=root_y * 0.124
)
version_combobox_ctk.set(version["version"])
version_combobox_ctk.place(relx=0.343, rely=0.848, relwidth=0.313)
set_opacity(version_combobox_ctk, color="#000001", value=0.9)
version_combobox = CTkScrollableDropdown(
    version_combobox_ctk,
    values=[],
    justify="left",
    height=root_y,
    fg_color=lighten_dominant_5,
    button_color=lighten_dominant_10,
    hover_color=lighten_dominant_15,
    command=set_version,
    font=get_dynamic_font("Segoe UI", 13),
    groups = [
        {"name": "Forge", "pattern": r"(?i)(?<!neo)forge.*"},
        {"name": "Fabric", "pattern": r"(?i).*fabric-loader.*"},
        {"name": "OptiFine", "pattern": r"(?i).*optifine.*"},
        {"name": "NeoForge", "pattern": r"(?i).*neoforge.*"},
        {"name": "Quilt", "pattern": r"(?i).*quilt.*"},
        {"name": "Minecraft",
         "pattern": r"(?i)^(?!.*(?:forge|fabric-loader|optifine|neoforge|quilt)).*"}
    ]
)
version_combobox.search_entry.configure(font=get_dynamic_font("Segoe UI", 23),
                                        text_color=user_color,
                                        corner_radius=20,
                                        border_width=0,
                                        fg_color=lighten_dominant_10)


launch_button = ctk.CTkButton(
    root,
    text=language_manager.get("main.buttons.launch_game"),
    command=lambda: threading.Thread(target=launch_game).start(),
    hover_color=lighten_dominant_5,
    fg_color=lighten_dominant_10,
    font=get_dynamic_font("Segoe UI", 20, "bold"),
    corner_radius=25,
    bg_color="#000001",
    text_color=user_color,
)
launch_button.place(relx=0.671, rely=0.848, relwidth=0.313, relheight=0.124)
set_opacity(launch_button, color="#000001", value=0.9)

for i in root, crash_window:
    hPyT.title_bar_color.set(i, dominant_color)
    hPyT.title_bar_text_color.set(i, "#000000" if user_color == "black" else "#FFFFFF")

ctk.set_appearance_mode(theme_type)

root.after(0, thread_load_versions)

blackout_frame.lift()
settings_frame.lift()

root.bind("<Configure>", lambda event: relative_center(), add="+")

root.after(0, lambda: show_tab(tabs[0]))

log(f"Done! ({perf_counter() - start_time:.2f} s)")

if not IS_INTERNET:
    new_message(title=language_manager.get("messages.titles.warning"),
                message=language_manager.get("messages.texts.warning.no_internet"),
                icon="warning", option_1=language_manager.get("messages.answers.ok"))
    for c in (release_checkbox, snapshot_checkbox, old_alpha_check, old_beta_check, skins_ely_by_checkbox,
              install_loader):
        c.configure(state="disabled")