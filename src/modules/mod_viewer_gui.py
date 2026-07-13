from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *
    
    
class ModWidget(ctk.CTkFrame):
    def __init__(self, master, toggle_callback, delete_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.mod_path = None
        self.mod_info = {}
        self.toggle_callback = toggle_callback
        self.delete_callback = delete_callback
        self.icon_ctk_image = None
        placeholder = PIL.Image.new("RGBA", (78, 78), (0, 0, 0, 0))
        draw = PIL.ImageDraw.Draw(placeholder, "RGBA")
        draw.rounded_rectangle(
            (2, 2, 76, 76),
            radius=18,
            fill=(30, 30, 46, 255),
            outline=(137, 180, 250, 255),
            width=2
        )
        draw.ellipse((24, 54, 54, 64), fill=(0, 0, 0, 100))
        center_x, center_y = 39, 37
        s = 16
        h = 14

        p_center = (center_x, center_y)
        p_top = (center_x, center_y - s)
        p_bottom = (center_x, center_y + s)
        p_top_right = (center_x + h, center_y - s // 2)
        p_bottom_right = (center_x + h, center_y + s // 2)
        p_top_left = (center_x - h, center_y - s // 2)
        p_bottom_left = (center_x - h, center_y + s // 2)

        draw.polygon(
            [p_top, p_top_right, p_center, p_top_left],
            fill=(137, 180, 250, 255)
        )
        draw.polygon(
            [p_top_left, p_center, p_bottom, p_bottom_left],
            fill=(180, 190, 254, 255)
        )
        draw.polygon(
            [p_center, p_top_right, p_bottom_right, p_bottom],
            fill=(116, 142, 203, 255)
        )

        line_color = (30, 30, 46, 255)
        draw.line([p_center, p_top], fill=line_color, width=2)
        draw.line([p_center, p_bottom_left], fill=line_color, width=2)
        draw.line([p_center, p_bottom_right], fill=line_color, width=2)
        draw.ellipse((37, 27, 41, 31), fill=(255, 255, 255, 255))

        self.empty_icon_image = ctk.CTkImage(
            light_image=placeholder,
            dark_image=placeholder,
            size=(78, 78)
        )

        self.configure(corner_radius=24, fg_color="#1a1a1a", border_width=1, border_color="#333333")
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1, minsize=0)
        self.grid_columnconfigure(2, weight=0, minsize=220)
        self.grid_rowconfigure(0, weight=1)
        self._card_fg = "#1a1a1a"
        self._card_border = "#333333"
        self._card_hover_fg = "#222222"
        self._card_hover_border = "#555555"

        self._on_enter = lambda e: self.configure(fg_color=self._card_hover_fg, border_color=self._card_hover_border)
        self._on_leave = lambda e: self.configure(fg_color=self._card_fg, border_color=self._card_border)
        self.icon_label = ctk.CTkLabel(self, text="", image=self.empty_icon_image)
        self.icon_label.grid(row=0, column=0, rowspan=4, padx=(28, 20), pady=24, sticky="n")
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        self.content_frame.grid(row=0, column=1, rowspan=4, sticky="nsew", pady=24)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.name_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent", border_width=0)
        self.name_frame.grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.name_label = ctk.CTkLabel(
            self.name_frame,
            text="",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.name_label.pack(side="left")
        self.status_label = ctk.CTkLabel(
            self.name_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=12,
            padx=14,
            pady=4
        )
        self.status_label.pack(side="left", padx=(16, 0))
        self.jar_label = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#777777"
        )
        self.jar_label.grid(row=1, column=0, sticky="w", pady=2)
        self.details_label = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#aaaaaa"
        )
        self.details_label.grid(row=2, column=0, sticky="w", pady=4)
        self.desc_label = ctk.CTkLabel(
            self.content_frame,
            text="",
            wraplength=585,
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        )
        self.desc_label.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        self.btn_frame.grid(row=0, column=2, rowspan=4, padx=(0, 28), pady=24, sticky="ne")
        self.toggle_button = ctk.CTkButton(
            self.btn_frame,
            text="",
            width=170,
            height=42,
            border_width=0,
            font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=20
        )
        self.toggle_button.pack(pady=(0, 10))
        self.delete_button = ctk.CTkButton(
            self.btn_frame,
            text=language_manager.get("mod_viewer.delete"),
            width=170,
            height=42,
            border_width=0,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#cc2222",
            hover_color="#ee4444",
            corner_radius=20
        )
        self.delete_button.pack()
        self._bind_hover(self)

    def _bind_hover(self, widget):
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        for child in widget.winfo_children():
            self._bind_hover(child)

    def update_content(self, mod_info, is_disabled, mod_path):
        self.mod_info = mod_info
        self.mod_path = mod_path

        self.configure(
            fg_color="#1a1a1a",
            border_color="#333333"
        )
        self.name_label.configure(
            text=mod_info.get("name", ""),
            font=ctk.CTkFont(size=22, weight="bold")
        )
        if mod_info.get("_incompatible", False) and not os.path.basename(mod_path).lower().endswith(".disabled"):
            status_text = language_manager.get("mod_viewer.status.incompatible")
            status_color = "#ff8800"
            status_bg = "#3a2a1f"
        else:
            status_text = language_manager.get("mod_viewer.status.disabled") if is_disabled else language_manager.get("mod_viewer.status.active")
            status_color = "#ff4444" if is_disabled else "#22cc66"
            status_bg = "#3a1f1f" if is_disabled else "#1f3a2a"
        self.status_label.configure(
            text=status_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=status_color,
            fg_color=status_bg,
            corner_radius=12
        )
        self.jar_label.configure(
            text=mod_info.get("jar_name", ""),
            font=ctk.CTkFont(size=12)
        )
        loaders = mod_info.get("loaders", [])
        loaders_text = ", ".join(loaders) if loaders else language_manager.get("mod_viewer.unknown")
        game_versions = mod_info.get("game_versions", [])
        if game_versions:
            if isinstance(game_versions, list):
                mc_ver = ", ".join(game_versions)
            else:
                mc_ver = str(game_versions)
        else:
            mc_ver = language_manager.get("mod_viewer.unknown")
        details = f"{loaders_text} • {language_manager.get('mod_viewer.version')} {mod_info.get('version') or language_manager.get('mod_viewer.unknown')} • Minecraft: {mc_ver}"
        self.details_label.configure(
            text=details,
            font=ctk.CTkFont(size=14)
        )
        desc = mod_info.get("description") or language_manager.get("mod_viewer.no_description")
        if len(desc) > 240:
            desc = desc[:237] + "..."
        self.desc_label.configure(
            text=desc,
            font=ctk.CTkFont(size=14)
        )
        if mod_info.get("icon"):
            self.icon_ctk_image = ctk.CTkImage(
                light_image=mod_info["icon"],
                dark_image=mod_info["icon"],
                size=(78, 78)
            )
            self.icon_label.configure(image=self.icon_ctk_image, text="")
        else:
            self.icon_ctk_image = None
            self.icon_label.configure(image=self.empty_icon_image, text="")
        is_actually_disabled = os.path.basename(mod_path).lower().endswith(".disabled")
        if mod_info.get("_incompatible", False) and not is_actually_disabled:
            toggle_text = language_manager.get("mod_viewer.toggle.lock")
            toggle_color = "#0066ff"
            toggle_hover = "#3388ff"
        else:
            toggle_text = language_manager.get("mod_viewer.toggle.unlock") if is_actually_disabled else language_manager.get("mod_viewer.toggle.lock")
            toggle_color = "#ff8800" if is_actually_disabled else "#0066ff"
            toggle_hover = "#ffaa33" if is_actually_disabled else "#3388ff"
        self.toggle_button.configure(
            text=toggle_text,
            fg_color=toggle_color,
            hover_color=toggle_hover,
            corner_radius=20,
            width=170,
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=lambda: self.toggle_callback(self.mod_path)
        )
        self.delete_button.configure(
            fg_color="#cc2222",
            hover_color="#ee4444",
            corner_radius=20,
            width=170,
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=lambda: self.delete_callback(self.mod_path)
        )


class ModViewer(ctk.CTkFrame):
    def __init__(self):
        super().__init__(root, border_width=0)
        self.place_forget()

        self.configure(fg_color="#0f0f0f")
        self.items_per_page = 10
        self.current_page = 1
        self.search_query = ""
        self.search_after_id = None
        self.all_mod_files = []
        self.filtered_mod_files = []
        self.mod_cache = {}
        self.fps = LauncherConfig.FPS
        self._first_load_done = False
        self.mod_manager = None
        self.version_var = ctk.StringVar()

        top_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        top_frame.pack(fill="x", padx=25, pady=(20, 10))

        toolbar = ctk.CTkFrame(top_frame, fg_color="transparent", border_width=0)
        toolbar.pack(side="top", fill="x")
    
        self.refresh_btn = ctk.CTkButton(
            toolbar,
            text=language_manager.get("mod_viewer.refresh"),
            width=130,
            height=38,
            corner_radius=18,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.load_mods
        )
        self.refresh_btn.pack(side="left", padx=5)
    
        self.unlock_all_btn = ctk.CTkButton(
            toolbar,
            text=language_manager.get("mod_viewer.unlock_all"),
            width=150,
            height=38,
            corner_radius=18,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1a8a4a",
            hover_color="#22aa55",
            command=self.unlock_all
        )
        self.unlock_all_btn.pack(side="left", padx=5)
    
        self.lock_all_btn = ctk.CTkButton(
            toolbar,
            text=language_manager.get("mod_viewer.lock_all"),
            width=150,
            height=38,
            corner_radius=18,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#cc6600",
            hover_color="#dd7700",
            command=self.lock_all
        )
        self.lock_all_btn.pack(side="left", padx=5)
    
        version_frame = ctk.CTkFrame(toolbar, fg_color="transparent", border_width=0)
        version_frame.pack(side="left", padx=15)
    
        version_label = ctk.CTkLabel(
            version_frame,
            text=language_manager.get("mod_viewer.version"),
            font=ctk.CTkFont(size=14)
        )
        version_label.pack(side="left", padx=(0, 8))
    
        self.version_entry = ctk.CTkEntry(
            version_frame,
            width=120,
            height=38,
            font=ctk.CTkFont(size=14),
            textvariable=self.version_var
        )
        self.version_entry.pack(side="left", padx=(0, 8))
    
        self.incompatible_count_label = ctk.CTkLabel(
            toolbar,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ff8800"
        )
        self.incompatible_count_label.pack(side="left", padx=5)
    
        self.close_btn = ctk.CTkButton(
            top_frame,
            text="✕",
            width=38,
            height=38,
            corner_radius=19,
            fg_color="#252525",
            hover_color="#c42b1c",
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self.withdraw
        )
        self.close_btn.place(relx=1.0, x=-5, y=0, anchor="ne")

        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=30, pady=(0, 12))

        self.search_var = ctk.StringVar(value="")

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Industrial Craft 2",
            height=40,
            font=ctk.CTkFont(size=15),
            textvariable=self.search_var
        )
        self.search_entry.pack(fill="x", expand=True)

        self.search_var.trace_add("write", self.on_search_change)

        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#0f0f0f",
            border_width=0
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=30, pady=8)

        self.mod_widgets = []

        for _ in range(self.items_per_page):
            widget = ModWidget(
                self.scroll_frame,
                toggle_callback=self.toggle_disable,
                delete_callback=self.delete_mod,
                fg_color="#1a1a1a",
                border_color="#333333"
            )
            widget.pack(fill="x", padx=8, pady=12)
            widget.pack_forget()
            self.mod_widgets.append(widget)

        self.pagination_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            border_width=0
        )
        self.pagination_frame.pack(fill="x", padx=30, pady=(8, 20))

        self.pagination_inner = ctk.CTkFrame(
            self.pagination_frame,
            fg_color="transparent",
            border_width=0
        )
        self.pagination_inner.pack()

        self.prev_btn = ctk.CTkButton(
            self.pagination_inner,
            text="◀",
            width=50,
            state="disabled",
            height=32,
            border_width=0,
            command=self.prev_page
        )
        self.prev_btn.pack(side="left", padx=4)

        self.page_label = ctk.CTkLabel(
            self.pagination_inner,
            text="1 / 1",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.page_label.pack(side="left", padx=12)

        self.next_btn = ctk.CTkButton(
            self.pagination_inner,
            text="▶",
            state="disabled",
            width=50,
            border_width=0,
            height=32,
            command=self.next_page
        )
        self.next_btn.pack(side="left", padx=4)

    def check_compatibility(self):
        selected_version = self.version_var.get()
        if not selected_version:
            return
        for mod_file in self.all_mod_files:
            path_key = mod_file
            info = self.mod_cache.get(path_key)
            if not info:
                continue
            is_disabled = os.path.basename(mod_file).lower().endswith(".disabled")
            if is_disabled:
                continue
            game_versions = info.get("game_versions", [])
            if not game_versions:
                continue
        self.mod_manager = None
        self.load_mods()
    
    def on_search_change(self, *args):
        if self.search_after_id is not None:
            self.after_cancel(self.search_after_id)
        self.search_after_id = self.after(100, self.apply_search)

    def apply_search(self):
        self.scroll_frame._parent_canvas.yview_moveto(0)
        self.search_after_id = None
        self.search_query = self.search_var.get().strip().casefold()
        self.current_page = 1
        self.refresh_view()

    def load_mods(self):
        if not os.path.exists(self.mods_dir):
            os.makedirs(self.mods_dir, exist_ok=True)

        if self.mod_manager is None:
            self.mod_manager = ModManager(mods_path=self.mods_dir)
        
        self.mod_manager.files_name = {}
        self.mod_manager.results = {}
        self.mod_manager.hashes = []
        self.mod_manager.get_mods_info()
    
        mod_files = []
        for entry in os.listdir(self.mods_dir):
            full_path = os.path.join(self.mods_dir, entry)
            if os.path.isfile(full_path) and entry.lower().endswith((".jar", ".jar.disabled")):
                mod_files.append(full_path)
    
        def sort_key(p):
            mod_name = os.path.basename(p)
            search_name = mod_name
            if search_name.lower().endswith(".jar.disabled"):
                search_name = search_name[:-9]
            elif search_name.lower().endswith(".jar"):
                search_name = search_name[:-4]
    
            for sha1, data in self.mod_manager.results.items():
                data_name = data.get("jar_name", "")
                if data_name.lower().endswith(".jar.disabled"):
                    data_name = data_name[:-9]
                elif data_name.lower().endswith(".jar"):
                    data_name = data_name[:-4]
                if data_name == search_name:
                    return (data.get("name") or search_name).casefold()
            return search_name.casefold()
    
        self.all_mod_files = sorted(mod_files, key=sort_key)
    
        current_paths = set(self.all_mod_files)
        for cached_path in list(self.mod_cache.keys()):
            if cached_path not in current_paths:
                del self.mod_cache[cached_path]
    
        for mod_file in self.all_mod_files:
            path_key = mod_file
            mtime_ns = os.stat(mod_file).st_mtime_ns
            cached = self.mod_cache.get(path_key)
            if cached is None or cached.get("_mtime_ns") != mtime_ns:
                mod_name = os.path.basename(mod_file)
                search_name = mod_name
                if search_name.lower().endswith(".jar.disabled"):
                    search_name = search_name[:-9]
                elif search_name.lower().endswith(".jar"):
                    search_name = search_name[:-4]
    
                info = None
                for sha1, data in self.mod_manager.results.items():
                    data_name = data.get("jar_name", "")
                    if data_name.lower().endswith(".jar.disabled"):
                        data_name = data_name[:-9]
                    elif data_name.lower().endswith(".jar"):
                        data_name = data_name[:-4]
                    if data_name == search_name:
                        info = {
                            "name": data.get("name", mod_name),
                            "description": data.get("description"),
                            "version": data.get("version"),
                            "loaders": data.get("loaders", []),
                            "game_versions": data.get("game_versions", []),
                            "jar_name": mod_name,
                            "icon": data.get("icon"),
                            "dependencies": data.get("dependencies", [])
                        }
                        break
                if info is None:
                    info = {
                        "name": search_name,
                        "description": "",
                        "version": "",
                        "loaders": [],
                        "game_versions": [],
                        "jar_name": mod_name,
                        "icon": None,
                        "dependencies": []
                    }
                info["_mtime_ns"] = mtime_ns
                info["_search_blob"] = " ".join(
                    str(info.get(key, "")) for key in ("name", "jar_name", "description", "version")
                ).casefold()
                if info.get("loaders"):
                    info["_search_blob"] += " " + " ".join(info["loaders"]).casefold()
                if info.get("game_versions"):
                    if isinstance(info["game_versions"], list):
                        info["_search_blob"] += " " + " ".join(info["game_versions"]).casefold()
                    else:
                        info["_search_blob"] += " " + str(info["game_versions"]).casefold()
                self.mod_cache[path_key] = info
        self.lock_all_btn.configure(state="normal")
        self.unlock_all_btn.configure(state="normal")
        self.refresh_btn.configure(state="normal")
        self.search_entry.configure(state="normal")
        self.refresh_view()

    def refresh_view(self):
        query = self.search_query.casefold() if self.search_query else ""
        name_matches = []
        other_matches = []

        for mod_file in self.all_mod_files:
            path_key = mod_file
            info = self.mod_cache.get(path_key)

            if info is None:
                mod_name = os.path.basename(mod_file)
                info = {
                    "name": mod_name,
                    "description": "",
                    "version": "",
                    "loaders": [],
                    "game_versions": [],
                    "jar_name": mod_name,
                    "icon": None,
                    "dependencies": []
                }
                info["_search_blob"] = " ".join(
                    str(info.get(key, "")) for key in ("name", "jar_name", "description", "version")
                ).casefold()
                self.mod_cache[path_key] = info

            if not query:
                name_matches.append(mod_file)
                continue

            mod_name = str(info.get("name", "")).casefold()
            mod_stem = os.path.basename(mod_file).casefold().replace(".jar", "")

            if query in mod_name or query in mod_stem:
                name_matches.append(mod_file)
            elif query in info["_search_blob"]:
                other_matches.append(mod_file)

        filtered_files = name_matches + other_matches

        selected_version = self.version_var.get()
        incompatible_count = 0
        for mod_file in filtered_files:
            path_key = mod_file
            info = self.mod_cache.get(path_key)
            if not info:
                continue
            is_disabled = os.path.basename(mod_file).lower().endswith(".disabled")
            if is_disabled:
                continue
            if selected_version:
                game_versions = info.get("game_versions", [])
                if game_versions:
                    compatible = False
                    for constraint in game_versions:
                        if ModManager.check_version(selected_version, constraint):
                            compatible = True
                            break
                    if not compatible:
                        incompatible_count += 1
                        info["_incompatible"] = True
                    else:
                        info["_incompatible"] = False

        self.incompatible_count_label.configure(text=f"{language_manager.get("mod_viewer.incompatible_count")} {incompatible_count}" if incompatible_count > 0 else "")

        filtered_files.sort(key=lambda f: (
            0 if self.mod_cache.get(f, {}).get("_incompatible", False) and not os.path.basename(f).lower().endswith(".disabled") else 1,
            self.mod_cache.get(f, {}).get("name", os.path.basename(f)).casefold()
        ))

        self.filtered_mod_files = filtered_files
        total_items = len(filtered_files)
        total_pages = (total_items + self.items_per_page - 1) // self.items_per_page if total_items > 0 else 1

        if self.current_page > total_pages:
            self.current_page = total_pages
        if self.current_page < 1:
            self.current_page = 1

        start = (self.current_page - 1) * self.items_per_page
        end = start + self.items_per_page
        page_files = filtered_files[start:end]

        self.render_page(page_files, query)
        self.update_pagination(total_pages)

    def render_page(self, page_files, query):
        selected_version = self.version_var.get()
        if page_files:
            for idx, widget in enumerate(self.mod_widgets):
                if idx < len(page_files):
                    mod_file = page_files[idx]
                    path_key = mod_file
                    info = self.mod_cache.get(path_key)
                    if info is None:
                        mod_name = os.path.basename(mod_file)
                        info = {
                            "name": mod_name,
                            "description": "",
                            "version": "",
                            "loaders": [],
                            "game_versions": [],
                            "jar_name": mod_name,
                            "icon": None,
                            "dependencies": []
                        }
                        info["_search_blob"] = " ".join(
                            str(info.get(key, "")) for key in ("name", "jar_name", "description", "version")
                        ).casefold()
                        self.mod_cache[path_key] = info
                    is_disabled = os.path.basename(mod_file).lower().endswith(".disabled")
                    if selected_version and not is_disabled:
                        game_versions = info.get("game_versions", [])
                        if game_versions:
                            compatible = False
                            for constraint in game_versions:
                                if ModManager.check_version(selected_version, constraint):
                                    compatible = True
                                    break
                            if not compatible:
                                is_disabled = True
                                info["_incompatible"] = True
                            else:
                                info["_incompatible"] = False
                    widget.update_content(info, is_disabled, mod_file)
                    if not widget.winfo_ismapped():
                        widget.pack(fill="x", padx=8, pady=12)
                else:
                    widget.pack_forget()
        else:
            for widget in self.mod_widgets:
                widget.pack_forget()

    def update_pagination(self, total_pages):
        if total_pages <= 1:
            self.pagination_frame.pack_forget()
            return
        if not self.pagination_frame.winfo_ismapped():
            self.pagination_frame.pack(fill="x", padx=30, pady=(8, 20))
        self.page_label.configure(text=f"{self.current_page} / {total_pages}")
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages else "disabled")

    def prev_page(self):
        self.scroll_frame._parent_canvas.yview_moveto(0)
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_view()

    def next_page(self):
        self.scroll_frame._parent_canvas.yview_moveto(0)
        total_items = len(self.filtered_mod_files)
        total_pages = (total_items + self.items_per_page - 1) // self.items_per_page if total_items > 0 else 1
        if self.current_page < total_pages:
            self.current_page += 1
            self.refresh_view()

    def toggle_disable(self, mod_path):
        mod_name = os.path.basename(mod_path)
        mod_dir = os.path.dirname(mod_path)
        if mod_name.lower().endswith(".disabled"):
            new_path = os.path.join(mod_dir, mod_name[:-9])
        else:
            new_path = os.path.join(mod_dir, mod_name + ".disabled")
        os.rename(mod_path, new_path)
        self.mod_manager = None
        self.load_mods()

    def delete_mod(self, mod_path):
        mod_name = os.path.basename(mod_path)
        new_message(
            title=language_manager.get("messages.titles.warning"),
            message=f"{language_manager.get('mod_viewer.delete_confirm')}\n{mod_name}",
            icon="question",
            option_1=language_manager.get("messages.answers.no"),
            option_2=language_manager.get("messages.answers.yes")
        )
        if GuiOptions.msg.get() == language_manager.get("messages.answers.yes"):
            if os.path.exists(mod_path):
                os.remove(mod_path)
            self.mod_manager = None
            self.load_mods()

    def _unlock_all_worker(self):
        try:
            for mod_file in self.all_mod_files:
                mod_name = os.path.basename(mod_file)
                mod_dir = os.path.dirname(mod_file)
                if mod_name.lower().endswith(".jar.disabled"):
                    new_path = os.path.join(mod_dir, mod_name[:-9])
                    os.rename(mod_file, new_path)
            self.mod_manager = None
            self.load_mods()
        finally:
            self.lock_all_btn.configure(state="normal")
            self.unlock_all_btn.configure(state="normal")
            self.refresh_btn.configure(state="normal")
            self.search_entry.configure(state="normal")

    def unlock_all(self):
        self.lock_all_btn.configure(state="disabled")
        self.unlock_all_btn.configure(state="disabled")
        self.refresh_btn.configure(state="disabled")
        self.search_entry.configure(state="disabled")

        threading.Thread(target=self._unlock_all_worker, daemon=True).start()

    def lock_all(self):
        self.lock_all_btn.configure(state="disabled")
        self.unlock_all_btn.configure(state="disabled")
        self.refresh_btn.configure(state="disabled")
        self.search_entry.configure(state="disabled")

        threading.Thread(target=self._lock_all_worker, daemon=True).start()

    def _lock_all_worker(self):
        try:
            for mod_file in self.all_mod_files:
                if not mod_file.lower().endswith(".jar.disabled"):
                    os.rename(mod_file, mod_file + ".disabled")
            self.mod_manager = None
            self.load_mods()
        finally:
            self.lock_all_btn.configure(state="normal")
            self.unlock_all_btn.configure(state="normal")
            self.refresh_btn.configure(state="normal")
            self.search_entry.configure(state="normal")

    def deiconify(self):
        if self.winfo_viewable():
            return

        if not self._first_load_done:
            self.mod_cache = {}
            self.all_mod_files = []
            self.filtered_mod_files = []
            self.mod_manager = None
            self.lock_all_btn.configure(state="disabled")
            self.unlock_all_btn.configure(state="disabled")
            self.refresh_btn.configure(state="disabled")
            self.search_entry.configure(state="disabled")
            if LauncherConfig.version["profile"]:
                self.mods_dir = os.path.join(LaunchOptions.minecraft_path, "profiles", "profile_" + LauncherConfig.version["profile"], "mods")
            else:
                self.mods_dir = os.path.join(LaunchOptions.minecraft_path, "mods")
            threading.Thread(target=self.load_mods, daemon=True).start()
            self._first_load_done = True

        duration = 0.25
        steps = max(1, round(self.fps * duration))

        self.place(relwidth=1, relheight=1)
        self.lift()

        for i in range(steps):
            if not self.winfo_exists():
                break
            opacity = (i + 1) / steps
            set_opacity(self, color="#242424", value=opacity)
            self.update()
            time.sleep(duration / steps)

    def withdraw(self):
        if not self.winfo_viewable():
            return

        duration = 0.25
        steps = max(1, round(self.fps * duration))

        for i in range(steps - 1, -1, -1):
            if not self.winfo_exists():
                break
            opacity = i / steps
            set_opacity(self, color="#242424", value=opacity)
            self.update()
            time.sleep(duration / steps)

        set_opacity(self, color="#242424", value=1)
        self.place_forget()