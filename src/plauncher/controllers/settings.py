from collections.abc import Callable, Mapping
from typing import Any


class SettingsController:
    def __init__(
        self,
        *,
        blackout_frame: Any,
        settings_frame: Any,
        root: Any,
        gui_options: Any,
        content_frames: Mapping[str, Any],
        fps: int,
        opacity_setter: Callable[..., None],
        version_filter_vars: tuple[Any, Any, Any, Any],
        previous_version_filters: Callable[[], list[bool]],
        load_versions: Callable[[], None],
    ) -> None:
        self.blackout_frame = blackout_frame
        self.settings_frame = settings_frame
        self.root = root
        self.gui_options = gui_options
        self.content_frames = content_frames
        self.fps = fps
        self.opacity_setter = opacity_setter
        self.version_filter_vars = version_filter_vars
        self.previous_version_filters = previous_version_filters
        self.load_versions = load_versions

    def open_settings(self) -> None:
        self.blackout_frame.unbind("<Button-1>")
        self.animate_value(
            on_complete=lambda: self.blackout_frame.bind(
                "<Button-1>", lambda event: self.close_settings()
            )
        )

    def call_load_versions(self) -> None:
        current_filters = [variable.get() for variable in self.version_filter_vars]
        if current_filters != self.previous_version_filters():
            self.root.after_idle(self.load_versions)

    def close_settings(self) -> None:
        self.blackout_frame.unbind("<Button-1>")
        self.animate_value(
            (0.55, 0.3),
            (1, 0),
            on_complete=lambda: (
                self.blackout_frame.bind(
                    "<Button-1>", lambda event: self.close_settings()
                ),
                self.call_load_versions(),
            ),
        )

    def show_tab(self, name: str) -> None:
        if name == self.gui_options.select_page:
            return
        self.gui_options.select_page = name
        for key, frame in self.content_frames.items():
            if key == name:
                frame.place(relx=0.05, rely=0.25, relwidth=0.9, relheight=0.7)
            else:
                frame.place_forget()

    @staticmethod
    def ease_in_out_quad(value: float) -> float:
        if value < 0.5:
            return 2 * value * value
        return -1 + (4 - 2 * value) * value

    def animate_value(
        self,
        start: tuple[float, float] = (1, 0),
        end: tuple[float, float] = (0.55, 0.3),
        duration_ms: int = 250,
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        frames = max(1, round(self.fps * (duration_ms / 1000.0)))
        interval = max(1, int(duration_ms / frames))

        def step(frame_index: int) -> None:
            progress = frame_index / frames
            eased_progress = self.ease_in_out_quad(progress)
            current_position = start[0] + (end[0] - start[0]) * eased_progress
            current_opacity = start[1] + (end[1] - start[1]) * eased_progress
            self.settings_frame.place(relx=current_position)
            self.opacity_setter(self.blackout_frame, value=current_opacity)

            if frame_index < frames:
                self.settings_frame.after(interval, step, frame_index + 1)
            elif on_complete is not None:
                on_complete()

        step(0)
