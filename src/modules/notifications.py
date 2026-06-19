from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


class ToastNotification(ctk.CTkFrame):
    active_toasts: dict[ctk.CTk | ctk.CTkToplevel, list["ToastNotification"]] = {}

    def __init__(
            self,
            message: str,
            title: Optional[str] = None,
            master: ctk.CTk | ctk.CTkToplevel = None,
            toast_type: Literal["success", "error", "warning"] = "success",
            duration: int = 2500,
            slide_from: Literal["left", "right", "top", "bottom"] = "right",
            width: int = 360,
            height: int = 100,
            corner_radius: int = 20,
            fps: int = None
    ):
        if master is None:
            master = root

        if fps is None:
            fps = LauncherConfig.FPS

        master.update_idletasks()

        self.fps_delay = int(1000 / fps)
        self.w = width
        self.h = height

        schemes = {
            "success": {"accent": "#10b981", "bg": "#052e16", "text": "#ecfdf5", "icon": "✅"},
            "error": {"accent": "#ef4444", "bg": "#450a0a", "text": "#fef2f2", "icon": "❌"},
            "warning": {"accent": "#f59e0b", "bg": "#451a03", "text": "#fefce8", "icon": "⚠️"}
        }
        scheme = schemes[toast_type]

        self.accent_color = scheme["accent"]
        self.bg_color = scheme["bg"]
        self.text_color = scheme["text"]
        self.icon_text = scheme["icon"]

        if title is None:
            title_map = {"success": "Success", "error": "Error", "warning": "Warning"}
            title = title_map.get(toast_type, "Notification")

        super().__init__(
            master=master,
            fg_color=self.bg_color,
            corner_radius=corner_radius,
            width=self.w,
            height=self.h,
        )

        set_opacity(self, color="#242424")

        self.master_window = master
        self.duration = duration
        self.slide_from = slide_from
        self.slot = 0

        self.pack_propagate(False)

        self.accent_bar = ctk.CTkFrame(self, fg_color=self.accent_color, width=6, corner_radius=15)
        self.accent_bar.pack(side="left", fill="y", padx=(5, 3), pady=10)

        self.content = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        self.content.pack(side="left", fill="both", expand=True, padx=16, pady=12)

        self.icon_label = ctk.CTkLabel(
            self.content, text=self.icon_text, font=ctk.CTkFont(size=34),
            text_color=self.accent_color, width=44
        )
        self.icon_label.pack(side="left", padx=(0, 14))

        self.text_area = ctk.CTkFrame(self.content, fg_color="transparent", border_width=0)
        self.text_area.pack(side="left", fill="both", expand=True)

        self.title_label = ctk.CTkLabel(
            self.text_area, text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.text_color, anchor="w"
        )
        self.title_label.pack(anchor="w", fill="x")

        self.message_label = ctk.CTkLabel(
            self.text_area, text=message,
            font=ctk.CTkFont(size=13), text_color=self.text_color,
            anchor="w", justify="left", wraplength=self.w - 150
        )
        self.message_label.pack(anchor="w", fill="x", pady=(3, 0))

        self.close_label = ctk.CTkLabel(
            self, text="✕", font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.text_color, fg_color="transparent",
            width=32, height=32, cursor="hand2"
        )
        self.close_label.pack(side="right", padx=12, pady=12)

        self.close_label.bind("<Button-1>", lambda e: self.dismiss())
        self.close_label.bind("<Enter>", lambda e: self.close_label.configure(text_color=self.accent_color))
        self.close_label.bind("<Leave>", lambda e: self.close_label.configure(text_color=self.text_color))

        self._calculate_final_position()
        self._set_initial_position()

        if master not in ToastNotification.active_toasts:
            ToastNotification.active_toasts[master] = []
        ToastNotification.active_toasts[master].append(self)

        self.place(x=self.initial_x, y=self.initial_y)
        self.lift()
        self.animate_slide_in()
        self._dismiss_id = self.after(self.duration, self.start_dismiss)

    def _calculate_final_position(self):
        padding = 20
        mw = self.master_window.winfo_width()
        self.final_x = mw - self.w - padding

        base_y = padding

        active_for_master = ToastNotification.active_toasts.get(self.master_window, [])
        occupied_slots = {t.slot for t in active_for_master if hasattr(t, 'slot')}

        self.slot = 0
        while self.slot in occupied_slots:
            self.slot += 1

        offset = self.slot * (self.h + 12)
        self.final_y = base_y + offset

    def _set_initial_position(self):
        offset = 60
        if self.slide_from == "right":
            self.initial_x = self.final_x + self.w + offset
            self.initial_y = self.final_y
        elif self.slide_from == "left":
            self.initial_x = self.final_x - self.w - offset
            self.initial_y = self.final_y
        elif self.slide_from == "bottom":
            self.initial_x = self.final_x
            self.initial_y = self.final_y + self.h + offset
        elif self.slide_from == "top":
            self.initial_x = self.final_x
            self.initial_y = self.final_y - self.h - offset

    def animate_slide_in(self, start_time: Optional[float] = None, duration: float = 0.5):
        if start_time is None:
            start_time = time.time()

        elapsed = time.time() - start_time
        progress = min(elapsed / duration, 1.0)

        eased = 1 - (1 - progress) ** 2

        dx = self.final_x - self.initial_x
        dy = self.final_y - self.initial_y

        self.place_configure(
            x=self.initial_x + dx * eased,
            y=self.initial_y + dy * eased
        )

        if progress < 1.0:
            self.after(self.fps_delay, lambda: self.animate_slide_in(start_time, duration))
        else:
            self.place_configure(x=self.final_x, y=self.final_y)

    def start_dismiss(self):
        self.animate_slide_out()

    def animate_slide_out(self, start_time: Optional[float] = None, duration: float = 0.4):
        if start_time is None:
            start_time = time.time()

        elapsed = time.time() - start_time
        progress = min(elapsed / duration, 1.0)

        eased = progress ** 2

        dx = self.initial_x - self.final_x
        dy = self.initial_y - self.final_y

        self.place_configure(
            x=self.final_x + dx * eased,
            y=self.final_y + dy * eased
        )

        if progress < 1.0:
            self.after(self.fps_delay, lambda: self.animate_slide_out(start_time, duration))
        else:
            self._destroy_toast()

    def dismiss(self):
        if hasattr(self, "_dismiss_id"):
            try:
                self.after_cancel(self._dismiss_id)
            except:
                pass
        self.animate_slide_out()

    def _destroy_toast(self):
        if (self.master_window in ToastNotification.active_toasts and
                self in ToastNotification.active_toasts[self.master_window]):
            ToastNotification.active_toasts[self.master_window].remove(self)
            if not ToastNotification.active_toasts[self.master_window]:
                del ToastNotification.active_toasts[self.master_window]
        self.destroy()


def new_message(**kwargs):
    if GuiOptions.msg:
        GuiOptions.msg.get()

    if kwargs["icon"] == "cancel":
        log(kwargs["message"].replace("\n", " "), "ERROR", "window_utils")

    GuiOptions.msg = CTkMessagebox(
        **kwargs,
        master=root
    )
    GuiOptions.msg.lift()
    GuiOptions.msg.get()


class CTkMessagebox(ctk.CTkFrame):
    ICONS = {
        "check": None,
        "cancel": None,
        "info": None,
        "question": None,
        "warning": None
    }
    ICON_BITMAP = {}

    def __init__(self,
                 master: any = None,
                 width: int = 400,
                 height: int = 200,
                 title: str = "CTkMessagebox",
                 message: str = "This is a CTkMessagebox!",
                 option_1: str = "OK",
                 option_2: str = None,
                 option_3: str = None,
                 options=None,
                 icon: str = "info",
                 icon_size: tuple = None,
                 option_focus: Literal[1, 2, 3] = None):
        super().__init__(master)
        self.configure(fg_color="#242424")
        set_opacity(self, color="#242424")

        self.fps = LauncherConfig.FPS

        if not message:
            message = "None"
        if options is None:
            options = []
        self.master_window = master
        self.animation_complete = False
        self.destroyed = False

        self.blackout_frames = []
        if self.master_window:
            frame = ctk.CTkFrame(self.master_window, fg_color="black", border_width=0)
            if frame.winfo_exists():
                set_opacity(frame.winfo_id(), color="#242424", value=0)
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.blackout_frames.append(frame)
            for widget in self.master_window.winfo_children():
                if isinstance(widget, ctk.CTkFrame) and widget is not self:
                    frame_child = ctk.CTkFrame(widget, fg_color="black", border_width=0)
                    if frame_child.winfo_exists():
                        set_opacity(frame_child.winfo_id(), color="#242424", value=0)
                    frame_child.place(relx=0, rely=0, relwidth=1, relheight=1)
                    self.blackout_frames.append(frame_child)

        if self.winfo_exists():
            set_opacity(self.winfo_id(), color="#242424", value=0)

        self.width = 250 if width < 250 else width
        self.height = 150 if height < 150 else height
        self.place(relx=0.5, rely=0.5, relwidth=self.width/1000, relheight=self.height/562, anchor="center")

        self.fade = True
        if self.fade:
            self.fade = 20 if self.fade < 20 else self.fade

        if sys.platform.startswith("win"):
            default_cancel_button = "cross"
        elif sys.platform.startswith("darwin"):
            default_cancel_button = "circle"
        else:
            self.round_corners = 0
            default_cancel_button = "cross"

        self.lift()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.x = self.winfo_x()
        self.y = self.winfo_y()
        self._title = title
        if message is None:
            message = "None"
        else:
            self.message = message

        self.cancel_button = default_cancel_button
        self.round_corners = 15
        self.button_width = self.width / 4
        self.button_height = 28

        if self.button_height > self.height / 4:
            self.button_height = self.height / 4 - 20

        self.border_width = 1

        if type(options) is list and len(options) > 0:
            try:
                option_1 = options[-1]
                option_2 = options[-2]
                option_3 = options[-3]
            except IndexError:
                pass

        self.bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        self.fg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])

        default_button_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        self.button_color = (default_button_color, default_button_color, default_button_color)
        self.text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        self.title_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        self.bt_text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["text_color"])
        self.bt_hv_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["hover_color"])
        self.border_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["border_color"])
        self.dot_color = self.title_color

        if icon_size:
            self.size_height = icon_size[1] if icon_size[1] <= self.height - 100 else self.height - 100
            self.size = (icon_size[0], self.size_height)
        else:
            self.size = (self.height / 4, self.height / 4)

        self.icon = self.load_icon(icon, icon_size) if icon else None

        self.frame_top = ctk.CTkFrame(
            self,
            corner_radius=self.round_corners,
            width=self.width,
            border_width=self.border_width,
            fg_color=self.bg_color,
            border_color=self.border_color,
        )
        self.frame_top.grid(sticky="nswe")

        self.frame_top.grid_columnconfigure(0, weight=1)
        self.frame_top.grid_rowconfigure((0, 1, 2), weight=1)

        if self.cancel_button == "cross":
            self.button_close = ctk.CTkButton(
                self.frame_top,
                corner_radius=10,
                width=0,
                height=0,
                hover=False,
                border_width=0,
                text_color=self.dot_color,
                text="✕",
                fg_color="transparent",
                font=("Segoe UI", 13)
            )
            self.button_close.grid(row=0, column=5, sticky="ne", padx=5 + self.border_width, pady=5 + self.border_width)
        elif self.cancel_button == "circle":
            self.button_close = ctk.CTkButton(
                self.frame_top,
                corner_radius=10,
                width=10,
                height=10,
                hover=False,
                border_width=0,
                text="",
                fg_color=self.dot_color,
                font=("Segoe UI", 13)
            )
            self.button_close.grid(row=0, column=5, sticky="ne", padx=10, pady=10)

        self.title_label = ctk.CTkLabel(
            self.frame_top,
            width=1,
            text=self._title,
            text_color=self.title_color,
            font=("Segoe UI", 13)
        )
        self.title_label.grid(row=0, column=0, columnspan=6, sticky="nw", padx=(15, 30), pady=5)

        self.info = ctk.CTkButton(
            self.frame_top,
            width=1,
            height=self.height / 2,
            border_width=0,
            corner_radius=0,
            text=self.message,
            fg_color=self.fg_color,
            hover=False,
            text_color=self.text_color,
            image=self.icon,
            image_near_text=True,
            font=("Segoe UI", 13)
        )
        self.info._text_label.configure(wraplength=self.width / 1.3, justify="left", font=("Segoe UI", 11))
        self.info.grid(row=1, column=0, columnspan=6, sticky="nwes", padx=self.border_width)

        self.option_text_1 = option_1

        self.button_1 = ctk.CTkButton(
            self.frame_top,
            text=self.option_text_1,
            fg_color=self.button_color[0],
            width=self.button_width,
            text_color=self.bt_text_color,
            hover_color=self.bt_hv_color,
            height=self.button_height,
            font=("Segoe UI", 13)
        )

        self.option_text_2 = option_2
        if option_2:
            self.button_2 = ctk.CTkButton(
                self.frame_top,
                text=self.option_text_2,
                fg_color=self.button_color[1],
                width=self.button_width,
                text_color=self.bt_text_color,
                hover_color=self.bt_hv_color,
                height=self.button_height,
                font=("Segoe UI", 13)
            )

        self.option_text_3 = option_3
        if option_3:
            self.button_3 = ctk.CTkButton(
                self.frame_top,
                text=self.option_text_3,
                fg_color=self.button_color[2],
                width=self.button_width,
                text_color=self.bt_text_color,
                hover_color=self.bt_hv_color,
                height=self.button_height,
                font=("Segoe UI", 13)
            )

        self.frame_top.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        columns = [4, 2, 0]
        span = 2
        self.button_1.grid(row=2, column=columns[0], columnspan=span, sticky="news", padx=(0, 10), pady=10)
        if option_2:
            self.button_2.grid(row=2, column=columns[1], columnspan=span, sticky="news", padx=10, pady=10)
        if option_3:
            self.button_3.grid(row=2, column=columns[2], columnspan=span, sticky="news", padx=(10, 0), pady=10)

        self.grab_set()

        try:
            self.button_close.configure(command=self.button_event)
            self.button_1.configure(command=lambda: self.button_event(self.option_text_1))
            if option_2:
                self.button_2.configure(command=lambda: self.button_event(self.option_text_2))
            if option_3:
                self.button_3.configure(command=lambda: self.button_event(self.option_text_3))
        except AttributeError:
            pass

        if option_focus:
            self.option_focus = option_focus
            self.focus_button(self.option_focus)
        else:
            if not self.option_text_2 and not self.option_text_3:
                self.button_1.focus()
                self.button_1.bind("<Return>", lambda event: self.button_event(self.option_text_1))

        try:
            self.bind("<Escape>", lambda e: self.button_event())
        except Exception:
            pass

        if self.fade:
            self.fade_in()
        else:
            if self.winfo_exists():
                set_opacity(self.winfo_id(), color="#242424", value=1)

    def place_widget(self, widget, x=10, y=10, **args):
        if "master" in args:
            del args["master"]
        new_widget = widget(master=self.frame_top, **args)
        new_widget.place(x=x, y=y)
        return new_widget

    def focus_button(self, option_focus):
        try:
            self.selected_button = getattr(self, "button_" + str(option_focus))
            self.selected_button.focus()
            self.selected_button.configure(border_color=self.bt_hv_color, border_width=3)
            self.selected_option = getattr(self, "option_text_" + str(option_focus))
            self.selected_button.bind("<Return>", lambda event: self.button_event(self.selected_option))
        except AttributeError:
            return
        self.bind("<Left>", lambda e: self.change_left())
        self.bind("<Right>", lambda e: self.change_right())

    def change_left(self):
        if self.option_focus == 3:
            return
        self.selected_button.unbind("<Return>")
        self.selected_button.configure(border_width=0)
        if self.option_focus == 1:
            if self.option_text_2:
                self.option_focus = 2
        elif self.option_focus == 2:
            if self.option_text_3:
                self.option_focus = 3
        self.focus_button(self.option_focus)

    def change_right(self):
        if self.option_focus == 1:
            return
        self.selected_button.unbind("<Return>")
        self.selected_button.configure(border_width=0)
        if self.option_focus == 2:
            self.option_focus = 1
        elif self.option_focus == 3:
            self.option_focus = 2
        self.focus_button(self.option_focus)

    def load_icon(self, icon, icon_size):
        if icon not in self.ICONS or self.ICONS[icon] is None:
            if icon in ["check", "cancel", "info", "question", "warning"]:
                image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'icons', icon + '.png')
            else:
                image_path = icon
            if icon_size:
                size_height = icon_size[1] if icon_size[1] <= self.height - 100 else self.height - 100
                size = (icon_size[0], size_height)
            else:
                size = (self.height / 4, self.height / 4)
            self.ICONS[icon] = ctk.CTkImage(PIL.Image.open(image_path), size=size)
            self.ICON_BITMAP[icon] = PIL.ImageTk.PhotoImage(file=image_path)
        return self.ICONS[icon]

    def safe_set_opacity(self, widget, color, value):
        if widget and widget.winfo_exists():
            set_opacity(widget.winfo_id(), color=color, value=value)

    def fade_in(self):
        if self.blackout_frames:
            for frame in self.blackout_frames:
                if frame.winfo_exists():
                    frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        steps = max(1, round(self.fps * 0.25))
        for i in range(steps):
            if not self.winfo_exists() or self.destroyed:
                break
            opacity = (i + 1) / steps
            if self.blackout_frames:
                for frame in self.blackout_frames:
                    self.safe_set_opacity(frame, "#242424", opacity / 2)
            self.safe_set_opacity(self, "#242424", opacity)
            self.update()
            time.sleep(0.25 / steps)
        self.animation_complete = True

    def fade_out(self):
        steps = max(1, round(self.fps * 0.25))
        for i in range(steps):
            if not self.winfo_exists():
                break
            opacity = 1.0 - (i + 1) / steps
            if self.blackout_frames:
                for frame in self.blackout_frames:
                    self.safe_set_opacity(frame, "#242424", opacity / 2)
            self.safe_set_opacity(self, "#242424", opacity)
            self.update()
            time.sleep(0.25 / steps)

        if self.blackout_frames:
            for frame in self.blackout_frames:
                if frame.winfo_exists():
                    frame.place_forget()

    def get(self):
        if self.winfo_exists():
            self.master.wait_window(self)
        return self.event

    def button_event(self, event=None):
        if not self.animation_complete or self.destroyed:
            return
        self.destroyed = True
        try:
            self.button_close.configure(command=object)
            self.button_1.configure(command=object)
            if hasattr(self, "button_2"):
                self.button_2.configure(command=object)
            if hasattr(self, "button_3"):
                self.button_3.configure(command=object)
        except AttributeError:
            pass

        if self.fade:
            self.fade_out()

        self.grab_release()
        self.place_forget()
        self.destroy()

        self.event = event

        if self.master_window:
            self.after(10, self.master_window.focus_force)
