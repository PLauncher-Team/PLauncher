def set_icon_loader(e=None):
    if e:
        version_combobox_ctk.set(e)
        version["version"] = version_combobox_ctk.get().replace(language_manager.get("main.types_versions.not_completed"), "").replace(language_manager.get("main.types_versions.installed"), "")
        save_version(version)
    loader_string = version_combobox_ctk.get().lower()
    for i in "neoforge", "forge", "fabric", "quilt", "optifine":
        if i in loader_string:
            version_combobox_ctk.configure(dropdown_image=icons_loaders[i])
            break
    else:
        version_combobox_ctk.configure(dropdown_image=icons_loaders["minecraft"])


def new_message(**kwargs):
    global msg
    if msg:
        msg.get()
    
    if kwargs["icon"] == "cancel":
        log(kwargs["message"].replace("\n", " "), "ERROR")
    msg = CTkMessagebox(**kwargs, font=get_dynamic_font("Segoe UI", 13), master=root, bg_color=dominant_color,
                        fg_color=lighten_dominant_10,
                        button_hover_color=lighten_dominant_5,
                        button_color=lighten_dominant_10,
                        button_text_color=user_color, border_color=dominant_color, text_color=user_color,
                        title_color=user_color, fps=FPS)
    msg.lift()
    msg.get()


def snip_image(pil_image, left, top, right, bottom):
    resized_image = pil_image.resize((root_x, root_y))

    cropped_image = resized_image.crop((left, top, right, bottom))

    ctk_cropped_image = ctk.CTkImage(cropped_image, size=(right - left, bottom - top))

    return ctk_cropped_image


def center(work, x, y):
    POS_X = work.winfo_screenwidth() // 2 - x // 2
    POS_Y = work.winfo_screenheight() // 2 - y // 2
    CORD = f"{POS_X}+{POS_Y}"
    return CORD


def relative_center():
    if version_combobox.state() == "normal":
        version_combobox._withdraw()
    if msg and msg.winfo_exists() and msg.state() != 'withdrawn':
        hPyT.window_frame.center_relative(root, msg)


def ex():
    new_message(title=language_manager.get("messages.titles.warning"), message=language_manager.get("messages.texts.warning.exit"), icon="question",
                option_1=language_manager.get("messages.answers.no"), option_2=language_manager.get("messages.answers.yes"))
    if msg.get() == language_manager.get("messages.answers.yes"):
        stop_action()
        root.destroy()
        kernel32.ReleaseMutex(mutex)
        os._exit(0)
    else:
        msg.grab_release()


def get_dynamic_font(font_name, base_size, weight="normal"):
    scale = ((screen_width / 1920) + (screen_height / 1080)) / 2
    return (font_name, max(8, int(base_size * scale)), weight)


def get_max_refresh_rate():
    monitors = win32api.EnumDisplayMonitors()
    log(f"Обнаружено мониторов: {len(monitors)}")
    max_refresh = 0
    for monitor in monitors:
        monitor_info = win32api.GetMonitorInfo(monitor[0])
        device_name = monitor_info.get("Device")
        settings = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)
        current_refresh = getattr(settings, "DisplayFrequency", 0)

        if current_refresh > max_refresh:
            max_refresh = current_refresh

    return max_refresh if max_refresh != 0 else 60


def new_tooltip(**kwargs):
    CTkToolTip(**kwargs, x_offset=int(20*width_factor), y_offset=int(10*height_factor), bg_color=dominant_color, border_color=lighten_dominant_15)