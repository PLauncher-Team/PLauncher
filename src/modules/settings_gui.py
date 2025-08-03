def open_settings():
    """
    Open the settings panel with animation and disable blackout frame click during animation
    """
    threading.Thread(target=set_skin).start()
    blackout_frame.unbind("<Button-1>")
    animate_value(on_complete=lambda: blackout_frame.bind("<Button-1>", lambda a: close_settings()))


def call_load_versions():
    """
    Load versions if checkboxes state has changed
    """
    show_release: bool = release_var.get()
    show_snapshot: bool = snapshot_var.get()
    show_old_beta: bool = old_beta_var.get()
    show_old_alpha: bool = old_alpha_var.get()

    new_types_versions = [show_release, show_snapshot, show_old_beta, show_old_alpha]
    if new_types_versions != old_types_versions:
        root.after(0, load_versions)


def close_settings():
    """
    Close the settings panel with animation and call load_versions if necessary
    """
    blackout_frame.unbind("<Button-1>")
    animate_value([0.55, 0.3], [1, 0], on_complete=lambda: (
        blackout_frame.bind("<Button-1>", lambda a: close_settings()),
        call_load_versions()
    ))


def ease_in_out_quad(t: float) -> float:
    """
    Easing function for smooth animation transitions
    """
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t


def animate_indicator(target_relx: float, duration: int = 125, easing=None):
    """
    Animate the movement of the tab indicator to the specified relative x position
    """
    ease = easing or ease_in_out_quad
    info = indicator.place_info()
    start = float(info['relx'])
    distance = target_relx - start
    steps = max(1, duration * FPS // 1000)
    interval = max(1, 1000 // FPS)

    def step(i: int = 0):
        if i <= steps:
            t = i / steps
            current = start + distance * ease(t)
            indicator.place_configure(relx=current)
            indicator.update()
            if i < steps:
                button_frame.after(interval, lambda: step(i + 1))
        else:
            indicator.place_configure(relx=target_relx)

    step()


def show_tab(name: str):
    """
    Display the selected tab and animate the indicator; update tab button styles
    """
    global select_page
    if name == select_page:
        return
    select_page = name

    for key, frame in content_frames.items():
        if key == name:
            frame.place(relx=0.05, rely=0.25, relwidth=0.9, relheight=0.7)
        else:
            frame.place_forget()

    for idx, (n, btn) in enumerate(tab_buttons.items()):
        if n == name:
            btn.configure(fg_color=hover_color, text_color="gray")
            animate_indicator(idx * (1 / len(tabs)))
        else:
            btn.configure(fg_color=fg_color, text_color=text_color)


def animate_value(start: tuple = (1, 0), end: tuple = (0.55, 0.3), duration_ms: int = 250, on_complete=None):
    """
    Animate movement and opacity between two states over a specified duration
    """
    frames = int(FPS * (duration_ms / 1000.0))
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
