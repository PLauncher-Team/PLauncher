from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


class MinecraftSkinRenderer:
    def __init__(self, skin: PIL.Image.Image, height: float, slim: bool = False):
        self.skin = skin
        self.force_slim = slim
        self.height = height

    def _load_skin(self):
        width, height = self.skin.size
        if (width, height) not in [(64, 64), (64, 32)]:
            ToastNotification(
                title=language_manager.get("messages.titles.error"),
                message=language_manager.get("messages.texts.error.skin_load"),
                toast_type="error"
            )
            LauncherConfig.config["custom_skin"] = default_config["custom_skin"]
            label_skin.configure(image=None)
            return None
        return self.skin.convert("RGBA")

    def _composite_layer(self, base: PIL.Image.Image, overlay: PIL.Image.Image) -> PIL.Image.Image:
        result = base.copy()
        result.paste(overlay, (0, 0), overlay)
        return result

    def _detect_slim(self, skin: PIL.Image.Image) -> bool:
        width, height = skin.size
        if width != 64 or height != 64:
            return False
        for y in range(20, 32):
            if skin.getpixel((47, y))[3] != 0:
                return False
        return True

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

    def _render_front(self, faces: dict[str, PIL.Image.Image]) -> PIL.Image.Image:
        canvas = PIL.Image.new("RGBA", (16, 32), (0, 0, 0, 0))
        canvas.paste(faces['head_front'], (4, 0))
        canvas.paste(faces['body_front'], (4, 8))
        canvas.paste(faces['arm_front'], (0, 8))
        canvas.paste(faces['arm_front_left'], (12, 8))
        canvas.paste(faces['leg_front'], (4, 20))
        canvas.paste(faces['leg_front_left'], (8, 20))
        return canvas

    def create_view(self, skin: PIL.Image.Image, is_slim: bool = False) -> PIL.Image.Image:
        faces = self._extract_faces(skin, is_slim)
        return self._render_front(faces)

    def run(self):
        skin = self._load_skin()
        if not skin:
            return None
        auto_slim = self._detect_slim(skin) if skin.size == (64, 64) else False
        is_slim = self.force_slim or auto_slim
        front_view = self.create_view(skin, is_slim)
        size_obj = front_view.size
        ratio = self.height / size_obj[1]
        new_width = int(size_obj[0] * ratio)
        new_height = int(self.height)
        resized_image = front_view.resize((new_width, new_height), PIL.Image.Resampling.NEAREST)
        return ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(new_width, new_height))


def get_skin_png() -> PIL.Image.Image:
    try:
        log(f"Загрузка скина с Ely.by для пользователя: {username_entry.get()}")
        url = f'https://skinsystem.ely.by/skins/{username_entry.get()}.png'
        response = requests.get(url)
        response.raise_for_status()
        return PIL.Image.open(BytesIO(response.content))
    except Exception:
        return None


def set_skin():
    image_skin = None
    if LauncherConfig.config["default_skin"]:
        log("Использование стандартного скина")
    else:
        update_skin_button.configure(state="disabled")
        skins_ely_by_checkbox.configure(state="disabled")
        if LauncherConfig.IS_INTERNET and LauncherConfig.config["ely_by"]:
            image_skin = get_skin_png()
        elif LauncherConfig.config["custom_skin"]:
            if os.path.isfile(LauncherConfig.config["custom_skin"]):
                log(f"Загрузка пользовательского скина из: {LauncherConfig.config['custom_skin']}")
                image_skin = PIL.Image.open(LauncherConfig.config["custom_skin"])
            else:
                log(f"Файл пользовательского скина не найден: {LauncherConfig.config['custom_skin']}", level="WARNING")
                LauncherConfig.config["custom_skin"] = default_config["custom_skin"]

        if image_skin:
            ctk_image_skin = MinecraftSkinRenderer(image_skin, 360 * 0.6).run()
            label_skin.configure(image=ctk_image_skin)
            label_skin.update_idletasks()
        else:
            label_skin.configure(image=None)

        update_skin_button.configure(state="normal")
        if LauncherConfig.IS_INTERNET:
            skins_ely_by_checkbox.configure(state="normal")


def select_png_file():
    file_path = filedialog.askopenfilename(
        title=language_manager.get("settings.3_page.choice_png_file"),
        filetypes=[(language_manager.get("settings.3_page.png_skin"), "*.png")]
    )
    if not file_path:
        return
    old_path = LauncherConfig.config["custom_skin"]
    try:
        LauncherConfig.config["custom_skin"] = file_path
        set_skin()
        save_config()
    except Exception as e:
        log(f"Не удалось загрузить файл скина {file_path}: {e}", level="ERROR")
        LauncherConfig.config["custom_skin"] = old_path
        ToastNotification(
            title=language_manager.get("messages.titles.error"),
            message=language_manager.get("messages.texts.skin_select") + str(e),
            toast_type="error"
        )


def update_controls():
    if default_skin_var.get():
        update_skin_button.configure(state="disabled")
        select_skin_button.configure(state="disabled")
        skins_ely_by_checkbox.configure(state="disabled")
    else:
        if LauncherConfig.IS_INTERNET:
            update_skin_button.configure(state="normal")
            skins_ely_by_checkbox.configure(state="normal")

        if ely_by_var.get() and LauncherConfig.IS_INTERNET:
            select_skin_button.configure(state="disabled")
        else:
            select_skin_button.configure(state="normal")


