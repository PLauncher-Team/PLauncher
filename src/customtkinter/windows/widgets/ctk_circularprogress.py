from .core_rendering import CTkCanvas
from .theme import ThemeManager
from . import CTkFrame
from .appearance_mode.appearance_mode_tracker import AppearanceModeTracker
import tkinter as tk


class CTkCircularProgress(CTkFrame):
    def __init__(self, master, size=200, thickness=10, fg_color=None, progress_fg_color=None,
                 progress_color=None, text_color=None, font=None, start_angle=90, mode="determinate",
                 indeterminate_speed=2, text_template="{value}%", variable=None, animation_duration=300, **kwargs):
        super().__init__(master, **kwargs)

        self.size = size
        self.thickness = thickness
        self.start_angle = start_angle
        self.mode = mode
        self.indeterminate_speed = indeterminate_speed
        self.text_template = text_template
        self.variable = variable
        self.animation_duration = animation_duration

        self.font = ("Segoe UI", int(self.size * 0.15)) if font is None else font

        canvas_bg = fg_color if fg_color else self._apply_appearance_mode(self._fg_color)

        mode_digit = AppearanceModeTracker.appearance_mode
        self.fg_color = ThemeManager.theme["CTkProgressBar"]["fg_color"][mode_digit] if progress_fg_color is None else self._check_color_type(progress_fg_color)
        self.progress_color = ThemeManager.theme["CTkProgressBar"]["progress_color"][mode_digit] if progress_color is None else self._check_color_type(progress_color)
        self.text_color = ThemeManager.theme["CTkButton"]["text_color"][mode_digit] if text_color is None else self._check_color_type(text_color)

        self.canvas = CTkCanvas(
            self,
            width=size,
            height=size,
            bg=self._apply_appearance_mode(canvas_bg),
            highlightthickness=0
        )
        self.canvas.pack()

        self.padding = thickness // 2 + 2
        self.coord = (self.padding, self.padding, size - self.padding, size - self.padding)

        self.current_value = 0
        self.target_value = 0
        self.animation_running = False
        self.animation_after_id = None
        self.indeterminate_after_id = None

        self.draw_widget()

        if self.variable:
            self.variable.trace_add("write", self._on_variable_change)
            self.set_value(self.variable.get())

        if self.mode == "indeterminate":
            self.start_indeterminate()

    def draw_widget(self):
        self.canvas.delete("all")

        self.canvas.create_arc(self.coord, start=0, extent=359.9, style=tk.ARC,
                               outline=self.fg_color, width=self.thickness)

        self.progress_arc = self.canvas.create_arc(self.coord, start=self.start_angle, extent=0, style=tk.ARC,
                                                   outline=self.progress_color, width=self.thickness)

        formatted_text = self.text_template.format(value=0)
        self.text_id = self.canvas.create_text(self.size // 2, self.size // 2, text=formatted_text,
                                               font=self.font, fill=self.text_color)

    def set_value(self, value):
        value = max(0, min(value, 100))
        self.target_value = value

        if self.animation_duration > 0:
            self._animate_to_target()
        else:
            self.current_value = self.target_value
            self._update_arc_and_text()

    def _animate_to_target(self):
        if self.animation_running:
            if self.animation_after_id:
                self.after_cancel(self.animation_after_id)
                self.animation_after_id = None
            self.animation_running = False

        self.animation_running = True
        self._animate_step()

    def _animate_step(self):
        if abs(self.current_value - self.target_value) < 0.1:
            self.current_value = self.target_value
            self._update_arc_and_text()
            self.animation_running = False
            return

        diff = self.target_value - self.current_value
        total_frames = self.animation_duration / 16
        step = diff / total_frames

        if abs(step) < 0.05:
            step = 0.05 if diff > 0 else -0.05

        self.current_value += step

        if (step > 0 and self.current_value > self.target_value) or (step < 0 and self.current_value < self.target_value):
            self.current_value = self.target_value

        self._update_arc_and_text()
        self.animation_after_id = self.after(16, self._animate_step)

    def _update_arc_and_text(self):
        extent_degrees = -(self.current_value / 100) * 359.9
        self.canvas.itemconfig(self.progress_arc, extent=extent_degrees)

        formatted_text = self.text_template.format(value=int(self.current_value))
        self.canvas.itemconfig(self.text_id, text=formatted_text)

    def _on_variable_change(self, *args):
        if self.variable:
            self.set_value(self.variable.get())

    def start_indeterminate(self):
        self.mode = "indeterminate"
        if self.indeterminate_after_id:
            self.after_cancel(self.indeterminate_after_id)
        self._indeterminate_angle = 0
        self._animate_indeterminate()

    def stop_indeterminate(self):
        self.mode = "determinate"
        if self.indeterminate_after_id:
            self.after_cancel(self.indeterminate_after_id)
            self.indeterminate_after_id = None

    def _animate_indeterminate(self):
        if self.mode != "indeterminate":
            return

        self._indeterminate_angle = (self._indeterminate_angle + self.indeterminate_speed) % 360
        self.canvas.itemconfig(self.progress_arc, start=self.start_angle + self._indeterminate_angle, extent=120)
        self.canvas.itemconfig(self.text_id, text="")

        self.indeterminate_after_id = self.after(16, self._animate_indeterminate)

    def configure(self, size=None, thickness=None, fg_color=None, progress_color=None, text_color=None,
                  start_angle=None, mode=None, text_template=None, animation_duration=None, **kwargs):
        if size is not None:
            self.size = size
            self.canvas.configure(width=size, height=size)
            self.padding = self.thickness // 2 + 2
            self.coord = (self.padding, self.padding, size - self.padding, size - self.padding)

        if thickness is not None:
            self.thickness = thickness
            self.padding = self.thickness // 2 + 2
            self.coord = (self.padding, self.padding, self.size - self.padding, self.size - self.padding)

        if fg_color is not None:
            self.fg_color = self._check_color_type(fg_color)

        if progress_color is not None:
            self.progress_color = self._check_color_type(progress_color)

        if text_color is not None:
            self.text_color = self._check_color_type(text_color)

        if start_angle is not None:
            self.start_angle = start_angle

        if mode is not None:
            if mode == "indeterminate":
                self.start_indeterminate()
            else:
                self.stop_indeterminate()

        if text_template is not None:
            self.text_template = text_template

        if animation_duration is not None:
            self.animation_duration = animation_duration

        self.draw_widget()

        if self.current_value > 0:
            self.set_value(self.current_value)

        super().configure(**kwargs)