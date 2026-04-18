from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from context import *

class ToastNotification(ctk.CTkFrame):
    active_toasts: Dict[ctk.CTk | ctk.CTkToplevel, list["ToastNotification"]] = {}

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
            fps = FPS
        
        master.update_idletasks()

        self.fps_delay = int(1000 / fps)
        self.w = int(width * width_factor)
        self.h = int(height * height_factor)
        self.radius = int(corner_radius * scale)

        schemes = {
            "success": {"accent": "#10b981", "bg": "#052e16", "text": "#ecfdf5", "icon": "✅"},
            "error":   {"accent": "#ef4444", "bg": "#450a0a",  "text": "#fef2f2", "icon": "❌"},
            "warning": {"accent": "#f59e0b", "bg": "#451a03",  "text": "#fefce8", "icon": "⚠️"}
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
            corner_radius=self.radius,
            width=self.w,
            height=self.h,
        )
        
        set_opacity(self, color="#242424")
        
        self.master_window = master
        self.duration = duration
        self.slide_from = slide_from
        self.slot = 0

        self.pack_propagate(False)

        self.accent_bar = ctk.CTkFrame(self, fg_color=self.accent_color, width=int(6 * scale), corner_radius=0)
        self.accent_bar.pack(side="left", fill="y", padx=(3, 3), pady=int(10 * scale))

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True, padx=int(16 * scale), pady=int(12 * scale))

        self.icon_label = ctk.CTkLabel(
            self.content, text=self.icon_text, font=ctk.CTkFont(size=int(34 * scale)),
            text_color=self.accent_color, width=int(44 * scale)
        )
        self.icon_label.pack(side="left", padx=(0, int(14 * scale)))

        self.text_area = ctk.CTkFrame(self.content, fg_color="transparent")
        self.text_area.pack(side="left", fill="both", expand=True)

        self.title_label = ctk.CTkLabel(
            self.text_area, text=title,
            font=ctk.CTkFont(size=int(16 * scale), weight="bold"),
            text_color=self.text_color, anchor="w"
        )
        self.title_label.pack(anchor="w", fill="x")

        self.message_label = ctk.CTkLabel(
            self.text_area, text=message,
            font=ctk.CTkFont(size=int(13 * scale)), text_color=self.text_color,
            anchor="w", justify="left", wraplength=self.w - int(150 * scale)
        )
        self.message_label.pack(anchor="w", fill="x", pady=(int(3 * scale), 0))

        self.close_label = ctk.CTkLabel(
            self, text="✕", font=ctk.CTkFont(size=int(20 * scale), weight="bold"),
            text_color=self.text_color, fg_color="transparent",
            width=int(32 * scale), height=int(32 * scale), cursor="hand2"
        )
        self.close_label.pack(side="right", padx=int(12 * scale), pady=int(12 * scale))

        self.close_label.bind("<Button-1>", lambda e: self.dismiss())
        self.close_label.bind("<Enter>", lambda e: self.close_label.configure(text_color=self.accent_color))
        self.close_label.bind("<Leave>", lambda e: self.close_label.configure(text_color=self.text_color))

        for widget in (self, self.content, self.text_area, self.icon_label,
                       self.title_label, self.message_label, self.accent_bar):
            widget.bind("<Button-1>", lambda e: self.dismiss())

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


class CTkMessagebox(ctk.CTkToplevel):
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
                 border_width: int = 1,
                 border_color: str = "default",
                 button_color: str = "default",
                 bg_color: str = "default",
                 fg_color: str = "default",
                 text_color: str = "default",
                 title_color: str = "default",
                 button_text_color: str = "default",
                 button_width: int = None,
                 button_height: int = None,
                 cancel_button_color: str = None,
                 cancel_button: str = None,
                 button_hover_color: str = "default",
                 icon: str = "info",
                 icon_size: tuple = None,
                 corner_radius: int = 15,
                 justify: str = "right",
                 font: tuple = None,
                 header: bool = False,
                 topmost: bool = False,
                 fade_in_duration: bool = True,
                 fps: int = 60,
                 sound: bool = False,
                 wraplength: int = 0,
                 option_focus: Literal[1, 2, 3] = None,
                 factor_width: float = 1.0,
                 factor_height: float = 1.0):
        super().__init__(master)

        if options is None:
            options = []
        self.master_window = master
        self.animation_complete = False
        font_factor = (factor_width + factor_height) / 2
        width = int(width * factor_width)
        height = int(height * factor_height)
        border_width = int(border_width * font_factor)
        corner_radius = int(corner_radius * font_factor)
        if button_height is None:
            button_height = int(28 * factor_height)
        else:
            button_height = int(button_height * factor_height)
        if icon_size:
            icon_size = (int(icon_size[0] * factor_width), int(icon_size[1] * factor_height))
        if font and isinstance(font, tuple) and len(font) >= 2 and isinstance(font[1], (int, float)):
            font = (font[0], max(8, int(font[1] * font_factor))) + font[2:]
        self.withdraw()
        self.blackout_frames = []
        if self.master_window:
            frame = ctk.CTkFrame(self.master_window, fg_color="black")
            set_opacity(frame, 0)
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.blackout_frames.append(frame)
            for widget in self.master_window.winfo_children():
                if isinstance(widget, ctk.CTkToplevel) and widget is not self:
                    frame_child = ctk.CTkFrame(widget, fg_color="black")
                    set_opacity(frame_child, 0)
                    frame_child.place(relx=0, rely=0, relwidth=1, relheight=1)
                    self.blackout_frames.append(frame_child)

        self.attributes("-alpha", 0)

        self.width = 250 if width < 250 else width
        self.height = 150 if height < 150 else height
        if self.master_window is None:
            self.spawn_x = int((self.winfo_screenwidth() - self.width) / 2)
            self.spawn_y = int((self.winfo_screenheight() - self.height) / 2)
        else:
            self.master_window.update_idletasks()
            self.spawn_x = int(self.master_window.winfo_width() * 0.5
                               + self.master_window.winfo_x()
                               - 0.5 * self.width
                               + (7 * factor_width))
            self.spawn_y = int(self.master_window.winfo_height() * 0.5
                               + self.master_window.winfo_y()
                               - 0.5 * self.height
                               + (20 * factor_height))
        self.geometry(f"{self.width}x{self.height}+{self.spawn_x}+{self.spawn_y}")
        self.title(title)
        self.resizable(width=False, height=False)
        self.fade = fade_in_duration

        if self.fade:
            self.fade = 20 if self.fade < 20 else self.fade
            self.attributes("-alpha", 0)

        if not header:
            self.overrideredirect(1)

        if topmost:
            self.attributes("-topmost", True)
        else:
            self.transient(self.master_window)

        if sys.platform.startswith("win"):
            self.transparent_color = self._apply_appearance_mode(self.cget("fg_color"))
            self.attributes("-transparentcolor", self.transparent_color)
            default_cancel_button = "cross"
        elif sys.platform.startswith("darwin"):
            self.transparent_color = 'systemTransparent'
            self.attributes("-transparent", True)
            default_cancel_button = "circle"
        else:
            self.transparent_color = '#000001'
            self.round_corners = 0
            default_cancel_button = "cross"

        self.lift()

        self.config(background=self.transparent_color)
        self.protocol("WM_DELETE_WINDOW", self.button_event)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.x = self.winfo_x()
        self.y = self.winfo_y()
        self._title = title
        self.fps = fps
        if message is None:
            message = "None"
        else:
            self.message = message
        self.font = font
        self.justify = justify
        self.sound = sound
        self.cancel_button = cancel_button if cancel_button else default_cancel_button
        self.round_corners = corner_radius if corner_radius <= 30 else 30
        self.button_width = button_width if button_width else self.width / 4
        self.button_height = button_height

        if self.fade:
            self.attributes("-alpha", 0)

        if self.button_height > self.height / 4:
            self.button_height = self.height / 4 - 20
        self.dot_color = cancel_button_color

        self.border_width = border_width if border_width < 6 else 5

        if type(options) is list and len(options) > 0:
            try:
                option_1 = options[-1]
                option_2 = options[-2]
                option_3 = options[-3]
            except IndexError:
                pass

        if bg_color == "default":
            self.bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        else:
            self.bg_color = bg_color

        if self.dot_color == "transparent":
            self.dot_color = self.bg_color

        if fg_color == "default":
            self.fg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["top_fg_color"])
        else:
            self.fg_color = fg_color

        default_button_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])

        if sys.platform.startswith("win"):
            if self.bg_color == self.transparent_color or self.fg_color == self.transparent_color:
                self.configure(fg_color="#000001")
                self.transparent_color = "#000001"
                self.attributes("-transparentcolor", self.transparent_color)

        if button_color == "default":
            self.button_color = (default_button_color, default_button_color, default_button_color)
        else:
            if type(button_color) is tuple:
                if len(button_color) == 2:
                    self.button_color = (button_color[0], button_color[1], default_button_color)
                elif len(button_color) == 1:
                    self.button_color = (button_color[0], default_button_color, default_button_color)
                else:
                    self.button_color = button_color
            else:
                self.button_color = (button_color, button_color, button_color)

        if text_color == "default":
            self.text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        else:
            self.text_color = text_color

        if title_color == "default":
            self.title_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        else:
            self.title_color = title_color

        if button_text_color == "default":
            self.bt_text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["text_color"])
        else:
            self.bt_text_color = button_text_color

        if button_hover_color == "default":
            self.bt_hv_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["hover_color"])
        else:
            self.bt_hv_color = button_hover_color

        if border_color == "default":
            self.border_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["border_color"])
        else:
            self.border_color = border_color

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
            bg_color=self.transparent_color,
            fg_color=self.bg_color,
            border_color=self.border_color
        )
        self.frame_top.grid(sticky="nswe")

        if button_width:
            self.frame_top.grid_columnconfigure(0, weight=1)
        else:
            self.frame_top.grid_columnconfigure((1, 2, 3), weight=1)

        if button_height:
            self.frame_top.grid_rowconfigure((0, 1, 3), weight=1)
        else:
            self.frame_top.grid_rowconfigure((0, 1, 2), weight=1)

        if self.cancel_button == "cross":
            self.button_close = ctk.CTkButton(
                self.frame_top,
                corner_radius=10,
                width=0,
                height=0,
                hover=False,
                border_width=0,
                text_color=self.dot_color if self.dot_color else self.title_color,
                text="✕",
                fg_color="transparent"
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
                fg_color=self.dot_color if self.dot_color else "#c42b1c"
            )
            self.button_close.grid(row=0, column=5, sticky="ne", padx=10, pady=10)

        self.title_label = ctk.CTkLabel(
            self.frame_top,
            width=1,
            text=self._title,
            text_color=self.title_color,
            font=self.font
        )
        self.title_label.grid(row=0, column=0, columnspan=6, sticky="nw", padx=(15, 30), pady=5)

        self.info = ctk.CTkButton(
            self.frame_top,
            width=1,
            height=self.height / 2,
            corner_radius=0,
            text=self.message,
            font=self.font,
            fg_color=self.fg_color,
            hover=False,
            text_color=self.text_color,
            image=self.icon,
            image_near_text=True
        )
        self.info._text_label.configure(wraplength=self.width / 2, justify="left")
        self.info.grid(row=1, column=0, columnspan=6, sticky="nwes", padx=self.border_width)

        if wraplength > 0:
            self.info._text_label.configure(wraplength=wraplength)

        if self.info._text_label.winfo_reqheight() > self.height / 2:
            height_offset = int((self.info._text_label.winfo_reqheight()) - (self.height / 2) + self.height)
            self.geometry(f"{self.width}x{height_offset}")

        self.option_text_1 = option_1

        self.button_1 = ctk.CTkButton(
            self.frame_top,
            text=self.option_text_1,
            fg_color=self.button_color[0],
            width=self.button_width,
            font=self.font,
            text_color=self.bt_text_color,
            hover_color=self.bt_hv_color,
            height=self.button_height
        )

        self.option_text_2 = option_2
        if option_2:
            self.button_2 = ctk.CTkButton(
                self.frame_top,
                text=self.option_text_2,
                fg_color=self.button_color[1],
                width=self.button_width,
                font=self.font,
                text_color=self.bt_text_color,
                hover_color=self.bt_hv_color,
                height=self.button_height
            )

        self.option_text_3 = option_3
        if option_3:
            self.button_3 = ctk.CTkButton(
                self.frame_top,
                text=self.option_text_3,
                fg_color=self.button_color[2],
                width=self.button_width,
                font=self.font,
                text_color=self.bt_text_color,
                hover_color=self.bt_hv_color,
                height=self.button_height
            )
        if self.justify == "center":
            if button_width:
                columns = [4, 3, 2]
                span = 1
            else:
                columns = [4, 2, 0]
                span = 2
            if option_3:
                self.frame_top.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
                self.button_1.grid(row=2, column=columns[0], columnspan=span, sticky="news", padx=(0, 10), pady=10)
                self.button_2.grid(row=2, column=columns[1], columnspan=span, sticky="news", padx=10, pady=10)
                self.button_3.grid(row=2, column=columns[2], columnspan=span, sticky="news", padx=(10, 0), pady=10)
            elif option_2:
                self.frame_top.columnconfigure((0, 5), weight=1)
                columns = [2, 3]
                self.button_1.grid(row=2, column=columns[0], sticky="news", padx=(0, 5), pady=10)
                self.button_2.grid(row=2, column=columns[1], sticky="news", padx=(5, 0), pady=10)
            else:
                if button_width:
                    self.frame_top.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
                else:
                    self.frame_top.columnconfigure((0, 2, 4), weight=2)
                self.button_1.grid(row=2, column=columns[1], columnspan=span, sticky="news", padx=(0, 10), pady=10)

        elif self.justify == "left":
            self.frame_top.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
            if button_width:
                columns = [0, 1, 2]
                span = 1
            else:
                columns = [0, 2, 4]
                span = 2
            if option_3:
                self.button_1.grid(row=2, column=columns[2], columnspan=span, sticky="news", padx=(0, 10), pady=10)
                self.button_2.grid(row=2, column=columns[1], columnspan=span, sticky="news", padx=10, pady=10)
                self.button_3.grid(row=2, column=columns[0], columnspan=span, sticky="news", padx=(10, 0), pady=10)
            elif option_2:
                self.button_1.grid(row=2, column=columns[1], columnspan=span, sticky="news", padx=10, pady=10)
                self.button_2.grid(row=2, column=columns[0], columnspan=span, sticky="news", padx=(10, 0), pady=10)
            else:
                self.button_1.grid(row=2, column=columns[0], columnspan=span, sticky="news", padx=(10, 0), pady=10)
        else:
            self.frame_top.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
            if button_width:
                columns = [5, 4, 3]
                span = 1
            else:
                columns = [4, 2, 0]
                span = 2
            self.button_1.grid(row=2, column=columns[0], columnspan=span, sticky="news", padx=(0, 10), pady=10)
            if option_2:
                self.button_2.grid(row=2, column=columns[1], columnspan=span, sticky="news", padx=10, pady=10)
            if option_3:
                self.button_3.grid(row=2, column=columns[2], columnspan=span, sticky="news", padx=(10, 0), pady=10)

        if header:
            self.title_label.configure(text="")
            self.title_label.grid_configure(pady=0)
            self.button_close.configure(text_color=self.bg_color)
            self.frame_top.configure(corner_radius=0)
        self.grab_set()

        if self.sound:
            self.bell()
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
            self.deiconify()
            self.attributes("-alpha", 1)

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
        if not sys.platform.startswith("darwin"):
            self.after(200, lambda: self.iconphoto(False, self.ICON_BITMAP[icon]))
        return self.ICONS[icon]

    def fade_in(self):
        if self.blackout_frames:
            for frame in self.blackout_frames:
                frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        steps = max(1, round(self.fps * 0.25))
        self.deiconify()
        for i in range(steps):
            if not self.winfo_exists():
                break
            opacity = (i + 1) / steps
            if self.blackout_frames:
                for frame in self.blackout_frames:
                    set_opacity(frame, value=opacity/2)
            self.attributes("-alpha", opacity)
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
                    set_opacity(frame, value=opacity/2)
            self.attributes("-alpha", opacity)
            self.update()
            time.sleep(0.25 / steps)

        if self.blackout_frames:
            for frame in self.blackout_frames:
                frame.place_forget()

    def get(self):
        if self.winfo_exists():
            self.master.wait_window(self)
        return self.event

    def button_event(self, event=None):
        if not self.animation_complete:
            return
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
        self.destroy()

        self.event = event

        if self.master_window:
            self.after(10, self.master_window.focus_force)