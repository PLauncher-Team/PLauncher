# Class responsible for rendering Minecraft skins into front-facing images
class MinecraftSkinRenderer:
    def __init__(self, skin: PIL.Image.Image, height: float, slim: bool = False):
        self.skin = skin
        self.force_slim = slim
        self.height = height

    # Validates skin size and converts to RGBA
    def _load_skin(self):
        width, height = self.skin.size
        if (width, height) not in [(64, 64), (64, 32)]:
            new_message(
                title=language_manager.get("messages.titles.error"),
                message=language_manager.get("messages.texts.error.skin_load"),
                icon="cancel",
                option_1=language_manager.get("messages.answers.ok")
            )
            config["custom_skin"] = default_config["custom_skin"]
            label_skin.configure(image=None)
            return
        return self.skin.convert("RGBA")

    # Combines overlay layer with base layer using alpha compositing
    def _composite_layer(self, base: PIL.Image.Image, overlay: PIL.Image.Image) -> PIL.Image.Image:
        result = base.copy()
        result.paste(overlay, (0, 0), overlay)
        return result

    # Detects whether the skin is a slim model based on transparency
    def _detect_slim(self, skin: PIL.Image.Image) -> bool:
        width, height = skin.size
        if width != 64 or height != 64:
            return False
        for y in range(20, 32):
            if skin.getpixel((47, y))[3] != 0:
                return False
        return True

    # Extracts face regions from the skin depending on format and model type
    def _extract_faces(self, skin: PIL.Image.Image, is_slim: bool = False) -> dict[str, PIL.Image.Image]:
        faces = {}
        width, height = skin.size

        if height == 32:
            faces['head_front'] = skin.crop((8, 8, 16, 16))
            faces['body_front'] = skin.crop((20, 20, 28, 32))
            faces['arm_front'] = skin.crop((44, 20, 48, 32))
            faces['arm_front_left'] = skin.crop((40, 20, 44, 32))
            faces['leg_front'] = skin.crop((4, 20, 8, 32))
            faces['leg_front_left'] = skin.crop((0, 20, 4, 32))
        elif height == 64:
            faces['head_front'] = self._composite_layer(skin.crop((8, 8, 16, 16)), skin.crop((40, 8, 48, 16)))
            faces['body_front'] = self._composite_layer(skin.crop((20, 20, 28, 32)), skin.crop((20, 36, 28, 48)))
            if is_slim:
                faces['arm_front'] = self._composite_layer(skin.crop((44, 20, 47, 32)), skin.crop((44, 36, 47, 48)))
                faces['arm_front_left'] = self._composite_layer(skin.crop((36, 52, 39, 64)), skin.crop((52, 52, 55, 64)))
            else:
                faces['arm_front'] = self._composite_layer(skin.crop((44, 20, 48, 32)), skin.crop((44, 36, 48, 48)))
                faces['arm_front_left'] = self._composite_layer(skin.crop((36, 52, 40, 64)), skin.crop((52, 52, 56, 64)))
            faces['leg_front'] = self._composite_layer(skin.crop((4, 20, 8, 32)), skin.crop((4, 36, 8, 48)))
            faces['leg_front_left'] = self._composite_layer(skin.crop((20, 52, 24, 64)), skin.crop((4, 52, 8, 64)))
        return faces

    # Renders a full front view from extracted face parts
    def _render_front(self, faces: dict[str, PIL.Image.Image]) -> PIL.Image.Image:
        canvas = PIL.Image.new("RGBA", (16, 32), (0, 0, 0, 0))
        canvas.paste(faces['head_front'], (4, 0))
        canvas.paste(faces['body_front'], (4, 8))
        canvas.paste(faces['arm_front'], (0, 8))
        canvas.paste(faces['arm_front_left'], (12, 8))
        canvas.paste(faces['leg_front'], (4, 20))
        canvas.paste(faces['leg_front_left'], (8, 20))
        return canvas

    # Combines extraction and rendering steps
    def create_view(self, skin: PIL.Image.Image, is_slim: bool = False) -> PIL.Image.Image:
        faces = self._extract_faces(skin, is_slim)
        return self._render_front(faces)

    # Main method to generate CTkImage from skin
    def run(self):
        skin = self._load_skin()
        if not skin:
            return
        auto_slim = self._detect_slim(skin) if skin.size == (64, 64) else False
        is_slim = self.force_slim or auto_slim
        front_view = self.create_view(skin, is_slim)
        size_obj = front_view.size
        ratio = self.height / size_obj[1]
        new_width = int(size_obj[0] * ratio)
        new_height = int(self.height)
        resized_image = front_view.resize((new_width, new_height), PIL.Image.Resampling.NEAREST)
        return ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(new_width, new_height))


# Downloads skin PNG from ely.by
def get_skin_png(nickname: str) -> PIL.Image.Image | None:
    try:
        url = f'http://skinsystem.ely.by/skins/{nickname}.png'
        response = requests.get(url)
        response.raise_for_status()
        return PIL.Image.open(BytesIO(response.content))
    except Exception:
        label_skin.configure(image=None)


# Sets the current skin based on user settings
def set_skin():
    global label_skin
    if config["default_skin"]:
        label_skin.configure(image=None)
    else:
        update_skin_button.configure(state="disabled")
        skins_ely_by_checkbox.configure(state="disabled")
        image_skin = None
        if IS_INTERNET and config["ely_by"]:
            image_skin = get_skin_png(username_entry.get())
        elif config["custom_skin"]:
            if os.path.isfile(config["custom_skin"]):
                image_skin = PIL.Image.open(config["custom_skin"])
            else:
                config["custom_skin"] = default_config["custom_skin"]
                label_skin.configure(image=None)
        else:
            label_skin.configure(image=None)

        if image_skin:
            ctk_image_skin = MinecraftSkinRenderer(image_skin, settings_y * 0.6).run()
            root.after(0, lambda: label_skin.configure(image=ctk_image_skin))
            label_skin.update()
        update_skin_button.configure(state="normal")
        if IS_INTERNET:
            skins_ely_by_checkbox.configure(state="normal")


# Opens file dialog to select PNG skin file
def select_png_file():
    file_path = filedialog.askopenfilename(
        title=language_manager.get("settings.3_page.choice_png_file"),
        filetypes=[(language_manager.get("settings.3_page.png_skin"), "*.png")]
    )
    if not file_path:
        return
    old_path = config["custom_skin"]
    try:
        config["custom_skin"] = file_path
        set_skin()
        save_config(config)
    except Exception as e:
        excepthook(*sys.exc_info())
        config["custom_skin"] = old_path
        new_message(
            title=language_manager.get("messages.titles.error"),
            message=language_manager.get("messages.texts.skin_select") + str(e),
            icon="cancel",
            option_1=language_manager.get("messages.answers.ok")
        )


# Updates UI controls based on skin settings and internet state
def update_controls():
    if default_skin_var.get():
        update_skin_button.configure(state="disabled")
        select_skin_button.configure(state="disabled")
        skins_ely_by_checkbox.configure(state="disabled")
    else:
        if IS_INTERNET:
            update_skin_button.configure(state="normal")
            skins_ely_by_checkbox.configure(state="normal")

        if ely_by_var.get() and IS_INTERNET:
            select_skin_button.configure(state="disabled")
        else:
            select_skin_button.configure(state="normal")


# Class that creates a resource pack from a skin
class MinecraftTexturePackCreator:
    def __init__(self, mc_folder: str, skin_path: str, pack_name: str = "PLauncher skins"):
        self.mc_folder = mc_folder
        self.skin_path = skin_path
        self.pack_name = pack_name
        self.models = ["alex.png", "ari.png", "efe.png", "kai.png", "makena.png", "noor.png", "steve.png", "sunny.png", "zuri.png"]

    # Creates the resource pack structure and copies skin files
    def create_texture_pack(self) -> str:
        res_packs_dir = os.path.join(self.mc_folder, "resourcepacks")
        os.makedirs(res_packs_dir, exist_ok=True)

        res_pack_folder = os.path.join(res_packs_dir, self.pack_name)
        if os.path.exists(res_pack_folder):
            shutil.rmtree(res_pack_folder)
        os.makedirs(res_pack_folder, exist_ok=True)

        modern_entity_dir = os.path.join(res_pack_folder, "assets", "minecraft", "textures", "entity")
        os.makedirs(modern_entity_dir, exist_ok=True)

        player_slim_dir = os.path.join(res_pack_folder, "assets", "minecraft", "textures", "entity", "player", "slim")
        player_wide_dir = os.path.join(res_pack_folder, "assets", "minecraft", "textures", "entity", "player", "wide")
        os.makedirs(player_slim_dir, exist_ok=True)
        os.makedirs(player_wide_dir, exist_ok=True)

        shutil.copy(self.skin_path, os.path.join(modern_entity_dir, "steve.png"))
        shutil.copy(self.skin_path, os.path.join(modern_entity_dir, "alex.png"))

        for model_file in self.models:
            shutil.copy(self.skin_path, os.path.join(player_slim_dir, model_file))
            shutil.copy(self.skin_path, os.path.join(player_wide_dir, model_file))

        packmeta = {
            "pack": {
                "pack_format": 15,
                "description": "Resource pack skin"
            }
        }
        packmeta_path = os.path.join(res_pack_folder, "pack.mcmeta")
        with open(packmeta_path, "w", encoding="utf-8") as f:
            json.dump(packmeta, f, indent=4)

        return res_pack_folder

    # Adds the resource pack to options.txt
    def modify_options(self):
        options_path = os.path.join(self.mc_folder, "options.txt")
        if not os.path.exists(options_path):
            with open(options_path, "w", encoding="utf-8") as f:
                f.write("")

        with open(options_path, encoding="utf-8") as f:
            lines = f.readlines()

        lines = self._update_option_line(lines, "resourcePacks:", self.pack_name)
        lines = self._update_option_line(lines, "incompatibleResourcePacks:", self.pack_name)

        with open(options_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    # Updates specific key-value entries in options.txt
    def _update_option_line(self, lines: list[str], key: str, new_pack: str) -> list[str]:
        for i, line in enumerate(lines):
            if line.startswith(key):
                current_value = line[len(key):].strip()
                packs = json.loads(current_value) if current_value else []
                if not isinstance(packs, list):
                    packs = []
                if new_pack not in packs:
                    packs.append(new_pack)
                lines[i] = f'{key}{json.dumps(packs, ensure_ascii=False)}\n'
                return lines

        lines.append(f'{key}{json.dumps([new_pack], ensure_ascii=False)}\n')
        return lines

    # Runs full resource pack creation and configuration
    def run(self):
        self.create_texture_pack()
        self.modify_options()