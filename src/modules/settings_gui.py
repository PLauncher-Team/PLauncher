from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


def open_settings():
    blackout_frame.unbind("<Button-1>")
    animate_value(on_complete=lambda: blackout_frame.bind("<Button-1>", lambda a: close_settings()))


def call_load_versions():
    show_release: bool = release_var.get()
    show_snapshot: bool = snapshot_var.get()
    show_old_beta: bool = old_beta_var.get()
    show_old_alpha: bool = old_alpha_var.get()

    new_types_versions = [show_release, show_snapshot, show_old_beta, show_old_alpha]
    if new_types_versions != LaunchOptions.old_types_versions:
        root.after_idle(load_versions)


def close_settings():
    blackout_frame.unbind("<Button-1>")
    animate_value([0.55, 0.3], [1, 0], on_complete=lambda: (
        blackout_frame.bind("<Button-1>", lambda a: close_settings()),
        call_load_versions()
    ))


def ease_in_out_quad(t: float) -> float:
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t


def show_tab(name: str):
    if name == GuiOptions.select_page:
        return
    GuiOptions.select_page = name

    for key, frame in content_frames.items():
        if key == name:
            frame.place(relx=0.05, rely=0.25, relwidth=0.9, relheight=0.7)
        else:
            frame.place_forget()


def animate_value(start: tuple = (1, 0), end: tuple = (0.55, 0.3), duration_ms: int = 250, on_complete=None):
    frames = int(LauncherConfig.FPS * (duration_ms / 1000.0))
    interval = int(duration_ms / frames)

    def step(frame_index: int):
        t = frame_index / frames
        eased_t = ease_in_out_quad(t)

        current_pos = start[0] + (end[0] - start[0]) * eased_t
        current_opacity = start[1] + (end[1] - start[1]) * eased_t

        settings_frame.place(relx=current_pos)
        set_opacity(blackout_frame, value=current_opacity)

        if frame_index < frames:
            settings_frame.after(interval, step, frame_index + 1)
        else:
            if on_complete:
                on_complete()

    step(0)