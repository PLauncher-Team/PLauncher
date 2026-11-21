import json
import shutil
from pathlib import Path


class SkinTexturePackService:
    MODELS = (
        "alex.png",
        "ari.png",
        "efe.png",
        "kai.png",
        "makena.png",
        "noor.png",
        "steve.png",
        "sunny.png",
        "zuri.png",
    )

    def __init__(
        self,
        mc_folder: str | Path,
        skin_path: str | Path,
        pack_name: str = "PLauncher skins",
    ) -> None:
        self.minecraft_directory = Path(mc_folder)
        self.skin_path = Path(skin_path)
        self.pack_name = pack_name
        self.pack_directory = self.minecraft_directory / "resourcepacks" / pack_name

    def create_texture_pack(self) -> Path:
        if not self.skin_path.is_file():
            raise FileNotFoundError(self.skin_path)

        entity_directory = self.pack_directory / "assets" / "minecraft" / "textures" / "entity"
        slim_directory = entity_directory / "player" / "slim"
        wide_directory = entity_directory / "player" / "wide"

        if self.pack_directory.exists():
            shutil.rmtree(self.pack_directory)

        slim_directory.mkdir(parents=True, exist_ok=True)
        wide_directory.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.skin_path, entity_directory / "steve.png")
        shutil.copy2(self.skin_path, entity_directory / "alex.png")

        for model in self.MODELS:
            shutil.copy2(self.skin_path, slim_directory / model)
            shutil.copy2(self.skin_path, wide_directory / model)

        metadata = {
            "pack": {
                "pack_format": 15,
                "description": "Resource pack skin",
            }
        }
        (self.pack_directory / "pack.mcmeta").write_text(
            json.dumps(metadata, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        return self.pack_directory

    def modify_options(self) -> None:
        options_file = self.minecraft_directory / "options.txt"
        if not options_file.exists():
            options_file.write_text("", encoding="utf-8")

        lines = options_file.read_text(encoding="utf-8").splitlines(keepends=True)
        lines = self._update_option_line(lines, "resourcePacks:")
        lines = self._update_option_line(lines, "incompatibleResourcePacks:")
        options_file.write_text("".join(lines), encoding="utf-8")

    def _update_option_line(self, lines: list[str], key: str) -> list[str]:
        for index, line in enumerate(lines):
            if line.startswith(key):
                current_value = line[len(key):].strip()
                packs = json.loads(current_value) if current_value else []
                if not isinstance(packs, list):
                    packs = []
                if self.pack_name not in packs:
                    packs.append(self.pack_name)
                lines[index] = f"{key}{json.dumps(packs, ensure_ascii=False)}\n"
                return lines

        lines.append(f'{key}{json.dumps([self.pack_name], ensure_ascii=False)}\n')
        return lines

    def run(self) -> Path:
        self.create_texture_pack()
        self.modify_options()
        return self.pack_directory
