import customtkinter
import sys
import re

class CTkScrollableDropdown(customtkinter.CTkToplevel):

    def __init__(self, attach, x=None, y=None, button_color=None, height: int = 55, width: int = None,
                 fg_color=None, button_height: int = 20, justify="center", scrollbar_button_color=None,
                 scrollbar=True, scrollbar_button_hover_color=None, frame_border_width=0, values=[],
                 command=None, image_values=[], alpha: float = 0.95, frame_corner_radius=20, double_click=False,
                 resize=False, frame_border_color=None, text_color=None, autocomplete=False,
                 hover_color=None, pagination: bool = True, items_per_page: int = 50,
                 groups=None, **button_kwargs):

        super().__init__(master=attach.winfo_toplevel(), takefocus=1)

        self.y_pos = None
        self.width_new = None
        self.x_pos = None
        self.focus()
        self.lift()
        self.alpha = alpha
        self.attach = attach
        self.corner = frame_corner_radius
        self.padding = 0
        self.focus_something = False
        self.disable = False
        self.update()
        self.old_kwargs = None
        self.widgets = {}
        self.all_values = values.copy()
        self.values = values.copy()
        self.hide_flag = True
        self.pagination = pagination
        self.items_per_page = items_per_page
        self.current_page = 0
        self.filtered_values = None
        self.groups = groups
        self.current_group = 0

        if self.groups:
            self.group_names = [g["name"] for g in groups]
            self.group_patterns = [re.compile(g["pattern"]) for g in groups]
            self.grouped_values = {
                i: [v for v in self.all_values if self.group_patterns[i].search(v)]
                for i in range(len(self.groups))
            }

        if sys.platform.startswith("win"):
            self.after(100, lambda: self.overrideredirect(True))
            self.transparent_color = self._apply_appearance_mode(self._fg_color) if hasattr(self, '_fg_color') else "#FFFFFF"
            self.attributes("-transparentcolor", self.transparent_color)
        elif sys.platform.startswith("darwin"):
            self.overrideredirect(True)
            self.transparent_color = 'systemTransparent'
            self.attributes("-transparent", True)
            self.focus_something = True
        else:
            self.overrideredirect(True)
            self.transparent_color = '#000001'
            self.corner = 0
            self.padding = 18
            self.withdraw()

        self.hide_flag = True
        self.attach.bind('<Configure>', lambda e: self._withdraw() if not self.disable else None, add="+")
        self.attach.winfo_toplevel().bind('<Configure>', lambda e: self._withdraw() if not self.disable else None, add="+")
        self.attach.winfo_toplevel().bind("<ButtonPress>", lambda e: self._withdraw() if not self.disable else None, add="+")
        self.bind("<Escape>", lambda e: self._withdraw() if not self.disable else None, add="+")
        self.attributes('-alpha', 0)

        self.fg_color = customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"] if fg_color is None else fg_color
        self.scroll_button_color = customtkinter.ThemeManager.theme["CTkScrollbar"]["button_color"] if scrollbar_button_color is None else scrollbar_button_color
        self.scroll_hover_color = customtkinter.ThemeManager.theme["CTkScrollbar"]["button_hover_color"] if scrollbar_button_hover_color is None else scrollbar_button_hover_color
        self.frame_border_color = customtkinter.ThemeManager.theme["CTkFrame"]["border_color"] if frame_border_color is None else frame_border_color
        self.button_color = customtkinter.ThemeManager.theme["CTkFrame"]["top_fg_color"] if button_color is None else button_color
        self.text_color = customtkinter.ThemeManager.theme["CTkLabel"]["text_color"] if text_color is None else text_color
        self.hover_color = customtkinter.ThemeManager.theme["CTkButton"]["hover_color"] if hover_color is None else hover_color

        if not scrollbar:
            self.scroll_button_color = self.fg_color
            self.scroll_hover_color = self.fg_color

        if self.pagination:
            self.search_var = customtkinter.StringVar()
            self.search_var.trace_add('write', lambda *args: self.live_update(self.search_var.get()))
            self.search_entry = customtkinter.CTkEntry(self, textvariable=self.search_var)
            self.search_entry.pack(fill="x")

        if self.groups:
            self.group_frame = customtkinter.CTkFrame(self, fg_color=self.fg_color)
            self.group_frame.pack(fill="x", padx=5)
            
            self.group_buttons = []
            
            for idx, name in enumerate(self.group_names):
                btn = customtkinter.CTkButton(
                    self.group_frame,
                    text=name,
                    height=button_height,
                    fg_color=self.button_color,
                    text_color=self.text_color,
                    hover_color=self.hover_color,
                    command=lambda i=idx: self.switch_group(i),
                )
                self.group_buttons.append(btn)
            
            self.group_frame.bind("<Configure>", self._on_group_frame_configure, add="+")
            
            self.group_button_colors = [btn.cget("fg_color") for btn in self.group_buttons]
        
        self.frame = customtkinter.CTkScrollableFrame(
            self,
            bg_color=self.transparent_color,
            fg_color=self.fg_color,
            scrollbar_button_hover_color=self.scroll_hover_color,
            corner_radius=self.corner,
            border_width=frame_border_width,
            scrollbar_button_color=self.scroll_button_color,
            border_color=self.frame_border_color
        )
        self.frame._scrollbar.grid_configure(padx=3)
        self.frame.pack(expand=True, fill="both")

        if self.pagination:
            self.button_container = customtkinter.CTkFrame(self.frame, fg_color=self.fg_color)
            self.button_container.pack(expand=True, fill="both")
            self.pagination_frame = customtkinter.CTkFrame(self.frame, fg_color=self.fg_color)
            self.pagination_frame.pack(fill="x", side="bottom")
        else:
            self.button_container = self.frame

        self.dummy_entry = customtkinter.CTkEntry(self.frame, fg_color="transparent", border_width=0, height=1, width=1)
        self.no_match = customtkinter.CTkLabel(self.button_container, text="No Match")
        self.height = height
        self.height_new = height
        self.width = width
        self.command = command
        self.fade = False
        self.resize = resize
        self.autocomplete = autocomplete
        self.var_update = customtkinter.StringVar()
        self.appear = True

        if justify.lower() == "left":
            self.justify = "w"
        elif justify.lower() == "right":
            self.justify = "e"
        else:
            self.justify = "c"

        self.button_height = button_height
        self.image_values = None if len(image_values) != len(self.values) else image_values

        self.resizable(width=False, height=False)
        self.transient(self.master)
        if double_click or isinstance(self.attach, customtkinter.CTkEntry) or isinstance(self.attach, customtkinter.CTkComboBox):
            self.attach.bind('<Double-Button-1>', lambda e: self._iconify(), add="+")
        else:
            self.attach.bind('<Button-1>', lambda e: self._iconify(), add="+")
        if isinstance(self.attach, customtkinter.CTkComboBox):
            self.attach._canvas.tag_bind("right_parts", "<Button-1>", lambda e: self._iconify())
            self.attach._canvas.tag_bind("dropdown_arrow", "<Button-1>", lambda e: self._iconify())
            if self.command is None:
                self.command = self.attach.set
        if isinstance(self.attach, customtkinter.CTkOptionMenu):
            self.attach._canvas.bind("<Button-1>", lambda e: self._iconify())
            self.attach._text_label.bind("<Button-1>", lambda e: self._iconify())
            if self.command is None:
                self.command = self.attach.set

        self.attach.bind("<Destroy>", lambda _: self._destroy(), add="+")
        self.update_idletasks()
        self.x = x
        self.y = y

        if self.autocomplete:
            self.bind_autocomplete()

        self.withdraw()
        self.attributes("-alpha", self.alpha)

        if self.groups:
            self.switch_group(0)

        self._init_buttons()

    def _on_group_frame_configure(self, event):
        min_btn_width = 100
        cols = max(1, event.width // min_btn_width)
    
        for child in self.group_frame.grid_slaves():
            child.grid_forget()
    
        for idx, btn in enumerate(self.group_buttons):
            row = idx // cols
            col = idx % cols
            btn.grid(row=row, column=col, sticky="ew", padx=2, pady=2)
    
        for c in range(cols):
            self.group_frame.grid_columnconfigure(c, weight=1)

    def switch_group(self, idx):
        if idx == self.current_group:
            self.values = self.all_values.copy()
            self.current_group = None
        else:
            self.current_group = idx
            self.values = self.grouped_values[idx].copy()
        for i, btn in enumerate(self.group_buttons):
            if i == self.current_group:
                btn.configure(fg_color=self.hover_color)
            else:
                btn.configure(fg_color=self.group_button_colors[i])
        self.filtered_values = None
        self.current_page = 0
        self._init_buttons()
    
    def update_buttons(self, values_list):
        for i, value in enumerate(values_list):
            if i in self.widgets:
                btn, _ = self.widgets[i]
                btn.configure(text=value, command=lambda v=value: self._attach_key_press(v))
                btn.pack(fill="x", pady=2, padx=(self.padding, 0))
                self.widgets[i][1] = True
            else:
                btn = customtkinter.CTkButton(
                    self.button_container,
                    text=value,
                    font=("Segoe UI", 12),
                    command=lambda v=value: self._attach_key_press(v),
                    height=self.button_height,
                    fg_color=self.button_color,
                    text_color=self.text_color,
                    anchor=self.justify,
                    hover_color=self.hover_color
                )
                btn.pack(fill="x", pady=2, padx=(self.padding, 0))
                self.widgets[i] = [btn, True]
        i = len(values_list)
        while i in self.widgets:
            btn, visible = self.widgets[i]
            if visible:
                btn.pack_forget()
                self.widgets[i][1] = False
            i += 1

    def _destroy(self):
        self.after(500, self.destroy_popup)

    def _withdraw(self):
        if not self.winfo_exists():
            return
        if self.winfo_viewable() and self.hide_flag:
            self.withdraw()
        self.event_generate("<<Closed>>")
        self.hide_flag = True

    def _update(self, a, b, c):
        self.live_update(self.attach._entry.get())

    def bind_autocomplete(self):
        def appear(x):
            self.appear = True
        if isinstance(self.attach, customtkinter.CTkComboBox):
            self.attach._entry.configure(textvariable=self.var_update)
            self.attach._entry.bind("<Key>", appear)
            if self.values:
                self.attach.set(self.values[0])
            self.var_update.trace_add('write', self._update)
        if isinstance(self.attach, customtkinter.CTkEntry):
            self.attach.configure(textvariable=self.var_update)
            self.attach.bind("<Key>", appear)
            self.var_update.trace_add('write', self._update)

    def _init_buttons(self):
        if self.pagination:
            values_to_show = self.values[self.current_page * self.items_per_page:
                                         (self.current_page + 1) * self.items_per_page]
            self._update_pagination_buttons()
        else:
            values_to_show = self.values
        self.update_buttons(values_to_show)
        self.frame._parent_canvas.yview_moveto(0)

    def _update_pagination_buttons(self, filtered=False):
        if not self.pagination:
            return
        for child in self.pagination_frame.winfo_children():
            child.destroy()
        values_list = self.filtered_values if (filtered and self.filtered_values is not None) else self.values
        total_pages = (len(values_list) + self.items_per_page - 1) // self.items_per_page
        button_width = 30
        button_padding = 4
        available_width = self.pagination_frame.winfo_width() if self.pagination_frame.winfo_ismapped() else self.width_new
        if available_width < 1:
            available_width = self.attach.winfo_width() if self.width is None else self.width
        max_buttons_per_row = max(1, available_width // (button_width + button_padding))
        total_rows = (total_pages + max_buttons_per_row - 1) // max_buttons_per_row
        for row in range(total_rows):
            for col in range(max_buttons_per_row):
                page_index = row * max_buttons_per_row + col
                if page_index >= total_pages:
                    break
                state = "disabled" if page_index == self.current_page else "normal"
                btn = customtkinter.CTkButton(
                    self.pagination_frame,
                    text=str(page_index + 1),
                    width=button_width,
                    height=30,
                    fg_color=self.button_color,
                    text_color=self.text_color,
                    command=lambda p=page_index: self._change_page(p),
                    state=state
                )
                btn.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
        for col in range(max_buttons_per_row):
            self.pagination_frame.grid_columnconfigure(col, weight=1)

    def _change_page(self, page_index):
        self.current_page = page_index
        if self.filtered_values is not None:
            values_to_show = self.filtered_values[self.current_page * self.items_per_page:
                                                  (self.current_page + 1) * self.items_per_page]
        else:
            values_to_show = self.values[self.current_page * self.items_per_page:
                                         (self.current_page + 1) * self.items_per_page]
            self.update_buttons(values_to_show)
            self._update_pagination_buttons(filtered=bool(self.filtered_values))
            self.frame.update_idletasks()
            self.frame._parent_canvas.yview_moveto(len(values_to_show) / self.items_per_page)
    
    def destroy_popup(self):
        self.destroy()
        self.disable = True

    def place_dropdown(self):
        if not self.winfo_exists():
            return
        current_width = self.winfo_width()
        current_height = self.winfo_height()
        current_x_pos = self.winfo_x()
        current_y_pos = self.winfo_y()
        self.x_pos = self.attach.winfo_rootx() if self.x is None else self.x + self.attach.winfo_rootx()
        self.width_new = self.attach.winfo_width() if self.width is None else self.width
        if self.resize:
            displayed_items = len(self.filtered_values) if self.filtered_values is not None else len(self.values)
            if self.pagination:
                displayed_items = min(displayed_items, self.items_per_page)
            base_height = 50 if self.pagination else 35
            items_height = displayed_items * self.button_height
            self.height_new = items_height + base_height
        screen_height = self.winfo_screenheight()
        dropdown_bottom = self.attach.winfo_rooty() + self.height_new
        if dropdown_bottom > screen_height:
            self.y_pos = max(0, self.attach.winfo_rooty() - self.height_new)
        else:
            self.y_pos = self.attach.winfo_rooty() + self.attach.winfo_height()
        if (current_width != self.width_new
                or current_height != self.height_new
                or current_x_pos != self.x_pos
                or current_y_pos != self.y_pos):
            self.geometry(f"{self.width_new}x{self.height_new}+{self.x_pos}+{self.y_pos}")
            self.attributes('-alpha', self.alpha)
            self.update_idletasks()
            if self.pagination:
                self._update_pagination_buttons(filtered=bool(self.filtered_values))

    def _iconify(self):
        if self.attach.cget("state") == "disabled":
            return
        if self.disable:
            return
        if self.winfo_ismapped():
            self.hide_flag = False
        if self.hide_flag and self.values:
            self.event_generate("<<Opened>>")
            self.focus()
            self.hide_flag = False
            self.place_dropdown()
            self._deiconify()
        else:
            self.withdraw()
            self.hide_flag = True

    def _attach_key_press(self, k):
        if hasattr(self, "search_var"):
            self.search_var.set("")
        self.event_generate("<<Selected>>")
        self.fade = True
        if self.command:
            self.command()
        if hasattr(self, "search_var") and self.search_var.get().strip() != "":
            self.filtered_values = None
            self.current_page = 0
            self._init_buttons()
            if self.pagination:
                self.pagination_frame.pack(fill="x", side="bottom")
        self.fade = False
        self.withdraw()
        self.hide_flag = True

    def live_update(self, string=None):
        if self.disable or self.fade:
            return
        self.frame._parent_canvas.yview_moveto(0)
        if string and string.strip() != "":
            string = string.lower()
            filtered = [val for val in self.values if string in val.lower()]
            self.filtered_values = filtered
            if self.pagination:
                total_pages = (len(filtered) + self.items_per_page - 1) // self.items_per_page
                if self.current_page >= total_pages:
                    self.current_page = 0
                self._update_pagination_buttons(filtered=True)
                values_to_show = filtered[self.current_page * self.items_per_page:(self.current_page + 1) * self.items_per_page]
            else:
                values_to_show = filtered
            self.update_buttons(values_to_show)
            if not values_to_show:
                self.no_match = customtkinter.CTkLabel(self.button_container, text="No Match")
                self.no_match.pack(fill="x", pady=2, padx=(self.padding, 0))
            else:
                if hasattr(self, 'no_match') and self.no_match.winfo_exists():
                    self.no_match.pack_forget()
            if self.pagination:
                self.pagination_frame.pack(fill="x", side="bottom")
            self.place_dropdown()
        else:
            if self.pagination:
                self.pagination_frame.pack(fill="x", side="bottom")
            if hasattr(self, 'no_match') and self.no_match.winfo_exists():
                self.no_match.pack_forget()
            self.filtered_values = None
            self.current_page = 0
            self._init_buttons()
            self.place_dropdown()
            self.appear = False

    def insert(self, value, **kwargs):
        index = len(self.values)
        if index in self.widgets:
            btn, _ = self.widgets[index]
            btn.configure(text=value, command=lambda v=value: self._attach_key_press(v))
            btn.pack(fill="x", pady=2, padx=(self.padding, 0))
            self.widgets[index][1] = True
        else:
            btn = customtkinter.CTkButton(self.button_container,
                                          text=value,
                                          height=self.button_height,
                                          fg_color=self.button_color,
                                          text_color=self.text_color,
                                          hover_color=self.hover_color,
                                          anchor=self.justify,
                                          command=lambda v=value: self._attach_key_press(v),
                                          width=0
                                          **kwargs)
            btn.pack(fill="x", pady=2, padx=(self.padding, 0))
            self.widgets[index] = [btn, True]
        self.values.append(value)
        self.all_values.append(value)
        if self.groups:
            self.grouped_values[self.current_group].append(value)
        if self.pagination:
            self._update_pagination_buttons()

    def _deiconify(self):
        if self.values:
            self.deiconify()

    def popup(self, x=None, y=None):
        self.x = x
        self.y = y
        self.hide_flag = True
        self._iconify()

    def hide(self):
        self._withdraw()

    def configure(self, **kwargs):
        if self.old_kwargs == kwargs:
            return
        if "height" in kwargs:
            self.height = kwargs.pop("height")
            self.height_new = self.height
        if "alpha" in kwargs:
            self.alpha = kwargs.pop("alpha")
        if "width" in kwargs:
            self.width = kwargs.pop("width")
        if "fg_color" in kwargs:
            self.frame.configure(fg_color=kwargs.pop("fg_color"))
        if "values" in kwargs:
            self.all_values = kwargs.pop("values")
            self.values = self.all_values.copy()
            self.image_values = None
            self.current_page = 0
            self._init_buttons()
            if hasattr(self, "search_var"):
                self.search_var.set("")
            if self.groups:
                self.grouped_values = {
                    i: [v for v in self.all_values if self.group_patterns[i].search(v)]
                    for i in range(len(self.groups))
                }
                self.switch_group(self.current_group)
        if "image_values" in kwargs:
            self.image_values = kwargs.pop("image_values")
            self.image_values = None if len(self.image_values) != len(self.values) else self.image_values
            if self.image_values is not None:
                for i in range(len(self.values)):
                    self.widgets[i][0].configure(image=self.image_values[i])
        if "button_color" in kwargs:
            bc = kwargs.pop("button_color")
            for key in self.widgets:
                self.widgets[key][0].configure(fg_color=bc)
        if self.old_kwargs != kwargs:
            for key in self.widgets:
                self.widgets[key][0].configure(**kwargs)
        self.old_kwargs = kwargs
        self.master.update()
