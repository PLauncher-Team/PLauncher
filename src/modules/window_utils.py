from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


def center(work, x: int, y: int) -> str:
    POS_X = work.winfo_screenwidth() // 2 - x // 2
    POS_Y = work.winfo_screenheight() // 2 - y // 2
    CORD = f"{POS_X}+{POS_Y}"
    return CORD


def ex():
    new_message(
        title=language_manager.get("messages.titles.warning"),
        message=language_manager.get("messages.texts.warning.exit"),
        icon="question",
        option_1=language_manager.get("messages.answers.no"),
        option_2=language_manager.get("messages.answers.yes")
    )
    if GuiOptions.msg.get() == language_manager.get("messages.answers.yes"):
        root.destroy()
        kernel32.ReleaseMutex(mutex)
        os._exit(0)
    else:
        GuiOptions.msg.grab_release()


def get_refresh_rate() -> int:
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
    CTkToolTip(
        **kwargs,
        x_offset=20,
        y_offset=10,
        bg_color=dominant_color,
        border_color=lighten_dominant_15
    )


class VersionFrame(ctk.CTkFrame):
    def __init__(self, master):
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
            text=LauncherConfig.CURRENT_VERSION,
            font=("Segoe UI", 24, "bold"),
            text_color="white"
        )
        self.version_label.place(relx=0.5, rely=0.5, anchor="center")
        self.new_label = None
        threading.Thread(target=self._update_check, daemon=True).start()

    def is_newer_version(self, latest_tag: str, current_tag: str) -> bool:
        try:
            return packaging.version.Version(latest_tag.lstrip('v')) > packaging.version.Version(current_tag.lstrip('v'))
        except Exception:
            return False

    def check_update(self, current_version: str) -> str | bool:
        try:
            latest_tag = mcl.utils.get_github_tags("PLauncher-Team", "PLauncher")[0]
            if latest_tag and self.is_newer_version(latest_tag, current_version):
                log(f"Доступно обновление: {current_version} -> {latest_tag}", source="window_utils")
                return latest_tag
            else:
                return False
        except Exception as e:
            log(f"Ошибка получения информации о новой версии: {e}", source="window_utils")
            excepthook(*sys.exc_info())
            return False

    def open_download(self, event: object = None):
        webbrowser.open(self.url)

    def _update_check(self):
        new_tag = self.check_update(LauncherConfig.CURRENT_VERSION)
        if new_tag:
            self.after(0, lambda: self._display_new_version(new_tag))

    def _display_new_version(self, new_tag: str):
        self.version_label.configure(text=new_tag)
        self.version_label.place_configure(rely=0.2, anchor="n")
        self.new_label = ctk.CTkLabel(
            self,
            text="new version",
            font=("Segoe UI", 14, "bold"),
            text_color="#FFD700"
        )
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


def apply_hover_border():
    widget_list = [launch_button, version_combobox_ctk, username_entry, settings_button, mods_button, logs_button,
                   feedback_button, version_combobox.search_entry,
                   mod_viewer_window.search_entry, mod_viewer_window.refresh_btn, mod_viewer_window.lock_all_btn,
                   mod_viewer_window.unlock_all_btn, mod_viewer_window.close_btn, installed_versions_combobox_ctk, del_version, java_combobox,
                   memory_combobox, args_entry, open_folder, change_folder, update_skin_button, select_skin_button, choice_version_ctk, choice_loader,
                   install_loader, list_profiles, add_profile_Entry, add_profile_button, del_profile_button, rename_profile_button,
                   open_profile, del_java_button, back_btn, crash_window.ai_button]
    original_borders = {}

    for widget in widget_list:
        original_borders[widget] = widget.cget("border_width")
        widget.configure(border_width=0)
        widget.bind("<Enter>", lambda e, w=widget, orig=original_borders[widget]:
        w.configure(border_width=orig) if w.cget("state") != "disabled" else None)
        widget.bind("<Leave>", lambda e, w=widget: w.configure(border_width=0))
