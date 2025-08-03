def set_version(e: str = None):
    # Set selected version from combobox and save it
    if e:
        version_combobox_ctk.set(e)
        version["version"] = version_combobox_ctk.get() \
            .replace(language_manager.get("main.types_versions.not_completed"), "") \
            .replace(language_manager.get("main.types_versions.installed"), "")
        save_version(version)


def new_message(**kwargs):
    # Show a custom message box with logging support for cancel icon
    global msg
    if msg:
        msg.get()

    if kwargs["icon"] == "cancel":
        log(kwargs["message"].replace("\n", " "), "ERROR", "window_utils")

    msg = CTkMessagebox(
        **kwargs,
        font=get_dynamic_font("Segoe UI", 13),
        master=root,
        fps=FPS
    )
    msg.lift()
    msg.get()


def center(work, x: int, y: int) -> str:
    # Calculate centered screen coordinates for a window of size x by y
    POS_X = work.winfo_screenwidth() // 2 - x // 2
    POS_Y = work.winfo_screenheight() // 2 - y // 2
    CORD = f"{POS_X}+{POS_Y}"
    return CORD


def relative_center():
    # Center message box relative to main window
    if version_combobox.state() == "normal":
        version_combobox._withdraw()
    if msg and msg.winfo_exists() and msg.state() != 'withdrawn':
        hPyT.window_frame.center_relative(root, msg)


def ex():
    # Show exit confirmation and terminate app if confirmed
    new_message(
        title=language_manager.get("messages.titles.warning"),
        message=language_manager.get("messages.texts.warning.exit"),
        icon="question",
        option_1=language_manager.get("messages.answers.no"),
        option_2=language_manager.get("messages.answers.yes")
    )
    if msg.get() == language_manager.get("messages.answers.yes"):
        root.destroy()
        kernel32.ReleaseMutex(mutex)
        os._exit(0)
    else:
        msg.grab_release()


def get_dynamic_font(font_name: str, base_size: int, weight: str = "normal") -> tuple:
    # Return dynamically scaled font based on screen resolution
    scale = ((screen_width / 1920) + (screen_height / 1080)) / 2
    return (font_name, max(8, int(base_size * scale)), weight)


def get_refresh_rate() -> int:
    # Detect current monitor refresh rate
    monitors = win32api.EnumDisplayMonitors()
    max_refresh = 0

    monitor_info = win32api.GetMonitorInfo(monitors[0][0])
    device_name = monitor_info.get("Device")
    settings = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)
    current_refresh = getattr(settings, "DisplayFrequency", 0)

    if current_refresh > max_refresh:
        max_refresh = current_refresh

    return max_refresh if max_refresh != 0 else 60


def new_tooltip(**kwargs):
    # Create and display a tooltip with default styling
    CTkToolTip(
        **kwargs,
        x_offset=int(20 * width_factor),
        y_offset=int(10 * height_factor),
        bg_color=dominant_color,
        border_color=lighten_dominant_15
    )


class VersionFrame(ctk.CTkFrame):
    def __init__(self, master):
        # Initialize frame with version info and updater
        super().__init__(
            master,
            fg_color="#111111",
            corner_radius=20,
            border_width=2,
            border_color="#FFFFFF"
        )
        set_opacity(self, value=0.6, color="#242424")
        self.url = "https://github.com/PLauncher-Team/PLauncher/releases/latest"
        self.version_label = ctk.CTkLabel(
            self,
            text=CURRENT_VERSION,
            font=get_dynamic_font("Segoe UI", 24, "bold"),
            text_color="white"
        )
        self.version_label.place(relx=0.5, rely=0.5, anchor="center")
        self.new_label = None
        threading.Thread(target=self._update_check, daemon=True).start()

    def get_latest_version_by_redirect(self) -> str | None:
        # Follow GitHub redirect and extract latest version tag
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = requests.head(self.url, headers=headers, allow_redirects=True, timeout=10)
            resp.raise_for_status()
            return resp.url.rstrip('/').rsplit('/', 1)[-1]
        except Exception:
            return None

    def is_newer_version(self, latest_tag: str, current_tag: str) -> bool:
        # Compare semantic versions to check for update
        try:
            return packaging.version.Version(latest_tag.lstrip('v')) > packaging.version.Version(current_tag.lstrip('v'))
        except Exception:
            return False

    def check_update(self, current_version: str) -> str | bool:
        # Return latest tag if it is newer than current version
        latest_tag = self.get_latest_version_by_redirect()
        return latest_tag if latest_tag and self.is_newer_version(latest_tag, current_version) else False

    def open_download(self, event: object=None):
        # Open browser to download latest release
        webbrowser.open(self.url)

    def _update_check(self):
        # Background thread: check for new version and update label if needed
        new_tag = self.check_update(CURRENT_VERSION)
        if new_tag:
            log(f"A new version of the launcher has been detected: {new_tag}")
            self.after(0, lambda: self._display_new_version(new_tag))

    def _display_new_version(self, new_tag: str):
        # Visually display new version and enable clickable area
        self.version_label.configure(text=new_tag)
        self.version_label.place_configure(rely=0.2, anchor="n")
        self.new_label = ctk.CTkLabel(
            self,
            text="new version",
            font=get_dynamic_font("Segoe UI", 14, "bold"),
            text_color="#FFD700"
        )
        self.new_label.place(relx=0.5, rely=0.8, anchor="s")
        self._bind_click_area()

    def _bind_click_area(self):
        # Bind click events to version label and all children
        self._set_bind(self)
        for child in self.winfo_children():
            self._set_bind(child)

    def _set_bind(self, widget):
        # Set mouse bindings and cursor change
        widget.bind("<Button-1>", self.open_download)
        widget.configure(cursor="hand2")
        widget.bind("<Enter>", lambda e: self.configure(fg_color="#111111"))
        widget.bind("<Leave>", lambda e: self.configure(fg_color="#000001"))
