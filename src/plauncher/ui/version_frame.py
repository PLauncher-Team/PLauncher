import threading
import webbrowser

import customtkinter as ctk
import pywinstyles
from packaging.version import Version


class VersionFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        current_version: str,
        online: bool,
        launcher_api,
        logger,
    ):
        super().__init__(
            master,
            fg_color="#111111",
            corner_radius=20,
            border_width=2,
            border_color="#FFFFFF",
        )
        self.current_version = current_version
        self.online = online
        self.launcher_api = launcher_api
        self.logger = logger
        self.url = "https://github.com/PLauncher-Team/PLauncher/releases/latest"
        pywinstyles.set_opacity(self, value=0.6, color="#242424")
        self.version_label = ctk.CTkLabel(
            self,
            text=current_version,
            font=("Segoe UI", 24, "bold"),
            text_color="white",
        )
        self.version_label.place(relx=0.5, rely=0.5, anchor="center")
        self.new_label = None
        threading.Thread(target=self._update_check, daemon=True).start()

    @staticmethod
    def is_newer_version(latest_tag: str, current_tag: str) -> bool:
        try:
            return Version(latest_tag.lstrip("v")) > Version(current_tag.lstrip("v"))
        except Exception:
            return False

    def check_update(self) -> str | bool:
        if not self.online:
            return False
        try:
            latest_tag = self.launcher_api.utils.get_github_tags(
                "PLauncher-Team",
                "PLauncher",
            )[0]
            if latest_tag and self.is_newer_version(latest_tag, self.current_version):
                self.logger(
                    f"Доступно обновление: {self.current_version} -> {latest_tag}"
                )
                return latest_tag
            return False
        except Exception as error:
            self.logger(
                f"Ошибка получения информации о новой версии: {error}",
                "ERROR",
            )
            return False

    def open_download(self, event: object = None) -> None:
        webbrowser.open(self.url)

    def _update_check(self) -> None:
        new_tag = self.check_update()
        if new_tag:
            self.after(0, lambda: self._display_new_version(new_tag))

    def _display_new_version(self, new_tag: str) -> None:
        self.version_label.configure(text=new_tag)
        self.version_label.place_configure(rely=0.2, anchor="n")
        self.new_label = ctk.CTkLabel(
            self,
            text="new version",
            font=("Segoe UI", 14, "bold"),
            text_color="#FFD700",
        )
        self.new_label.place(relx=0.5, rely=0.8, anchor="s")
        self._bind_click_area()

    def _bind_click_area(self) -> None:
        self._set_bind(self)
        for child in self.winfo_children():
            self._set_bind(child)

    def _set_bind(self, widget) -> None:
        widget.bind("<Button-1>", self.open_download)
        widget.configure(cursor="hand2")
        widget.bind("<Enter>", lambda event: self.configure(fg_color="#111111"))
        widget.bind("<Leave>", lambda event: self.configure(fg_color="#000001"))
