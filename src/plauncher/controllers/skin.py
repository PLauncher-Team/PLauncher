from collections.abc import Callable, MutableMapping
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image


class MinecraftSkinRenderer:
    def __init__(self, skin: Image.Image, height: float, slim: bool = False) -> None:
        self.skin = skin
        self.force_slim = slim
        self.height = height

    @staticmethod
    def _composite_layer(base: Image.Image, overlay: Image.Image) -> Image.Image:
        result = base.copy()
        result.paste(overlay, (0, 0), overlay)
        return result

    @staticmethod
    def _detect_slim(skin: Image.Image) -> bool:
        width, height = skin.size
        if width != 64 or height != 64:
            return False
        return all(skin.getpixel((47, y))[3] == 0 for y in range(20, 32))

    def _extract_faces(self, skin: Image.Image, is_slim: bool) -> dict[str, Image.Image]:
        faces = {}
        _, height = skin.size
        if height == 32:
            faces["head_front"] = skin.crop((8, 8, 16, 16))
            faces["body_front"] = skin.crop((20, 20, 28, 32))
            faces["arm_front"] = skin.crop((44, 20, 48, 32))
            faces["arm_front_left"] = skin.crop((40, 20, 44, 32))
            faces["leg_front"] = skin.crop((4, 20, 8, 32))
            faces["leg_front_left"] = skin.crop((0, 20, 4, 32))
        else:
            faces["head_front"] = self._composite_layer(
                skin.crop((8, 8, 16, 16)), skin.crop((40, 8, 48, 16))
            )
            faces["body_front"] = self._composite_layer(
                skin.crop((20, 20, 28, 32)), skin.crop((20, 36, 28, 48))
            )
            arm_right_end = 47 if is_slim else 48
            arm_left_end = 39 if is_slim else 40
            faces["arm_front"] = self._composite_layer(
                skin.crop((44, 20, arm_right_end, 32)),
                skin.crop((44, 36, arm_right_end, 48)),
            )
            faces["arm_front_left"] = self._composite_layer(
                skin.crop((36, 52, arm_left_end, 64)),
                skin.crop((52, 52, 55 if is_slim else 56, 64)),
            )
            faces["leg_front"] = self._composite_layer(
                skin.crop((4, 20, 8, 32)), skin.crop((4, 36, 8, 48))
            )
            faces["leg_front_left"] = self._composite_layer(
                skin.crop((20, 52, 24, 64)), skin.crop((4, 52, 8, 64))
            )
        return faces

    def create_view(self, skin: Image.Image, is_slim: bool = False) -> Image.Image:
        faces = self._extract_faces(skin, is_slim)
        canvas = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
        canvas.paste(faces["head_front"], (4, 0))
        canvas.paste(faces["body_front"], (4, 8))
        canvas.paste(faces["arm_front"], (0, 8))
        canvas.paste(faces["arm_front_left"], (12, 8))
        canvas.paste(faces["leg_front"], (4, 20))
        canvas.paste(faces["leg_front_left"], (8, 20))
        return canvas

    def render(self) -> Image.Image:
        if self.skin.size not in {(64, 64), (64, 32)}:
            raise ValueError("Minecraft skin must be 64x64 or 64x32 pixels")
        skin = self.skin.convert("RGBA")
        auto_slim = self._detect_slim(skin) if skin.size == (64, 64) else False
        front_view = self.create_view(skin, self.force_slim or auto_slim)
        ratio = self.height / front_view.height
        new_size = (int(front_view.width * ratio), int(self.height))
        return front_view.resize(new_size, Image.Resampling.NEAREST)


class SkinController:
    def __init__(
        self,
        *,
        settings: MutableMapping[str, Any],
        default_skin: str,
        online: bool,
        username: Callable[[], str],
        skin_label: Any,
        update_button: Any,
        select_button: Any,
        ely_by_checkbox: Any,
        default_skin_variable: Any,
        ely_by_variable: Any,
        language_manager: Any,
        http_client: Any,
        file_dialog: Any,
        image_factory: Callable[[Image.Image], Any],
        notify_error: Callable[[str, str], None],
        logger: Callable[..., None],
        save_config: Callable[[], None],
    ) -> None:
        self.settings = settings
        self.default_skin = default_skin
        self.online = online
        self.username = username
        self.skin_label = skin_label
        self.update_button = update_button
        self.select_button = select_button
        self.ely_by_checkbox = ely_by_checkbox
        self.default_skin_variable = default_skin_variable
        self.ely_by_variable = ely_by_variable
        self.language_manager = language_manager
        self.http_client = http_client
        self.file_dialog = file_dialog
        self.image_factory = image_factory
        self.notify_error = notify_error
        self.logger = logger
        self.save_config = save_config

    def _text(self, key: str) -> str:
        return self.language_manager.get(key)

    def get_skin_image(self) -> Image.Image | None:
        username = self.username()
        try:
            self.logger(f"Загрузка скина с Ely.by для пользователя: {username}")
            response = self.http_client.get(
                f"https://skinsystem.ely.by/skins/{username}.png"
            )
            response.raise_for_status()
            with Image.open(BytesIO(response.content)) as image:
                return image.copy()
        except Exception:
            return None

    def set_skin(self) -> None:
        image_skin = None
        if self.settings["default_skin"]:
            self.logger("Использование стандартного скина")
        else:
            self.update_button.configure(state="disabled")
            self.ely_by_checkbox.configure(state="disabled")
            if self.online and self.settings["ely_by"]:
                image_skin = self.get_skin_image()
            elif self.settings["custom_skin"]:
                image_path = Path(self.settings["custom_skin"])
                if image_path.is_file():
                    self.logger(f"Загрузка пользовательского скина из: {image_path}")
                    with Image.open(image_path) as image:
                        image_skin = image.copy()
                else:
                    self.logger(
                        f"Файл пользовательского скина не найден: {image_path}",
                        level="WARNING",
                    )
                    self.settings["custom_skin"] = self.default_skin

        rendered = None
        if image_skin is not None:
            try:
                rendered = self.image_factory(
                    MinecraftSkinRenderer(image_skin, 360 * 0.6).render()
                )
            except ValueError:
                self.notify_error(
                    self._text("messages.titles.error"),
                    self._text("messages.texts.error.skin_load"),
                )
                self.settings["custom_skin"] = self.default_skin

        self.skin_label.configure(image=rendered)
        if rendered is not None:
            self.skin_label.update_idletasks()
        if not self.settings["default_skin"]:
            self.update_button.configure(state="normal")
            if self.online:
                self.ely_by_checkbox.configure(state="normal")

    def select_skin_file(self) -> None:
        file_path = self.file_dialog.askopenfilename(
            title=self._text("settings.3_page.choice_png_file"),
            filetypes=[(self._text("settings.3_page.png_skin"), "*.png")],
        )
        if not file_path:
            return

        previous_path = self.settings["custom_skin"]
        try:
            self.settings["custom_skin"] = file_path
            self.set_skin()
            self.save_config()
        except Exception as error:
            self.logger(f"Не удалось загрузить файл скина {file_path}: {error}", level="ERROR")
            self.settings["custom_skin"] = previous_path
            self.notify_error(
                self._text("messages.titles.error"),
                self._text("messages.texts.skin_select") + str(error),
            )

    def update_controls(self) -> None:
        if self.default_skin_variable.get():
            self.update_button.configure(state="disabled")
            self.select_button.configure(state="disabled")
            self.ely_by_checkbox.configure(state="disabled")
            return

        if self.online:
            self.update_button.configure(state="normal")
            self.ely_by_checkbox.configure(state="normal")
        self.select_button.configure(
            state=(
                "disabled"
                if self.ely_by_variable.get() and self.online
                else "normal"
            )
        )
