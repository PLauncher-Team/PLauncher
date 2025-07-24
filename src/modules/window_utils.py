def set_version(e=None):
    if e:
        version_combobox_ctk.set(e)
        version["version"] = version_combobox_ctk.get().replace(language_manager.get("main.types_versions.not_completed"), "").replace(language_manager.get("main.types_versions.installed"), "")
        save_version(version)


def new_message(**kwargs):
    global msg
    if msg:
        msg.get()
    
    if kwargs["icon"] == "cancel":
        log(kwargs["message"].replace("\n", " "), "ERROR", "window_utils")
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


class VersionFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master,
                         fg_color="#111111",
                         corner_radius=20,
                         border_width=2,
                         border_color="#FFFFFF",
                         bg_color="#000001")
        set_opacity(self, value=0.6, color="#000001")
        self.url = "https://github.com/PLauncher-Team/PLauncher/releases/latest"
        self.version_label = ctk.CTkLabel(self,
                                          text=CURRENT_VERSION,
                                          font=get_dynamic_font("Segoe UI", 24, "bold"),
                                          text_color="white")
        self.version_label.place(relx=0.5, rely=0.5, anchor="center")
        self.new_label = None
        threading.Thread(target=self._update_check, daemon=True).start()

    def get_latest_version_by_redirect(self):
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = requests.head(self.url, headers=headers, allow_redirects=True, timeout=10)
            resp.raise_for_status()
            return resp.url.rstrip('/').rsplit('/', 1)[-1]
        except Exception:
            return None

    def is_newer_version(self, latest_tag: str, current_tag: str) -> bool:
        try:
            return packaging.version.Version(latest_tag.lstrip('v')) > packaging.version.Version(current_tag.lstrip('v'))
        except Exception:
            return False

    def check_update(self, current_version: str):
        latest_tag = self.get_latest_version_by_redirect()
        return latest_tag if latest_tag and self.is_newer_version(latest_tag, current_version) else False

    def open_download(self, event=None):
        webbrowser.open(self.url)

    def _update_check(self):
        new_tag = self.check_update(CURRENT_VERSION)
        if new_tag:
            log(f"A new version of the launcher has been detected: {new_tag}")
            self.after(0, lambda: self._display_new_version(new_tag))

    def _display_new_version(self, new_tag):
        self.version_label.configure(text=new_tag)
        self.version_label.place_configure(rely=0.2, anchor="n")
        self.new_label = ctk.CTkLabel(self,
                                      text="new version",
                                      font=get_dynamic_font("Segoe UI", 14, "bold"),
                                      text_color="#FFD700")
        self.new_label.place(relx=0.5, rely=0.8, anchor="s")
        self._bind_click_area()

    def _bind_click_area(self):
        self._set_bind(self)
        for child in self.winfo_children():
            self._set_bind(child)

    def _set_bind(self, widget):
        widget.bind("<Button-1>", self.open_download)
        widget.configure(cursor="hand2")
        widget.bind("<Enter>", lambda e: self.configure(fg_color="#111111"))
        widget.bind("<Leave>", lambda e: self.configure(fg_color="#000001"))