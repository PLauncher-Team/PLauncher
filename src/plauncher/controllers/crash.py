import sys
import threading
from collections.abc import Callable
from typing import Any

import customtkinter as ctk
from PIL import Image


class CrashLogWindow(ctk.CTkToplevel):
    def __init__(
        self,
        parent: ctk.CTk,
        *,
        language_manager: Any,
        language: str,
        online: bool,
        analyzer: Any,
        logger: Callable[[str], None],
        exception_handler: Callable[..., None],
        kill_thread: Callable[[threading.Thread], Any],
        center_window: Callable[[Any, int, int], str],
        titlebar_helper: Any,
        titlebar_color: str,
        header_color_setter: Callable[..., None],
    ) -> None:
        super().__init__(parent)
        self.language_manager = language_manager
        self.language = language
        self.analyzer = analyzer
        self.logger = logger
        self.exception_handler = exception_handler
        self.kill_thread = kill_thread
        self.center_window = center_window
        self.titlebar_helper = titlebar_helper
        self.titlebar_color = titlebar_color
        self.header_color_setter = header_color_setter
        self.withdraw()
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.title(self.language_manager.get("crash_log.title"))
        self.geometry("600x700")
        self.resizable(False, False)
        self.thread: threading.Thread | None = None
        self.message: str | None = None
        self.transient(parent)
        self.bind("<Map>", self._restore_titlebar_color)
        self.titlebar_helper.maximize_minimize_button.hide(self)

        top_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        top_frame.place(relx=0.0333, rely=0.0286, relwidth=0.9333, relheight=0.1143)
        logo = Image.open("png/GUI/bug.png")
        logo_image = ctk.CTkImage(light_image=logo, size=(32, 32))
        ctk.CTkLabel(
            top_frame, image=logo_image, fg_color="transparent"
        ).place(relx=0.0, relwidth=0.0571, relheight=0.64)
        ctk.CTkLabel(
            top_frame,
            text=self.language_manager.get("crash_log.error_log"),
            font=("Segoe UI", 25, "bold"),
            fg_color="transparent",
            anchor="w",
        ).place(relx=0.0714, relwidth=0.9286, relheight=0.60)

        self.log_textbox = ctk.CTkTextbox(
            self, font=("Segoe UI", 13), state="disabled", wrap="word"
        )
        self.log_textbox.place(
            relx=0.0333, rely=0.1286, relwidth=0.9333, relheight=0.35
        )
        self.solution_frame = ctk.CTkFrame(self, border_width=2, corner_radius=12)
        self.solution_frame.place(
            relx=0.0333, rely=0.5, relwidth=0.9333, relheight=0.35
        )
        ctk.CTkLabel(
            self.solution_frame,
            text=self.language_manager.get("crash_log.solution_title"),
            font=("Segoe UI", 18, "bold"),
            fg_color="transparent",
            anchor="w",
        ).place(relx=0.025, rely=0.02, relwidth=0.95, relheight=0.12)
        self.solution_textbox = ctk.CTkTextbox(
            self.solution_frame,
            font=("Segoe UI", 13),
            state="disabled",
            wrap="word",
            corner_radius=8,
            activate_scrollbars=True,
        )
        self.solution_textbox.place(
            relx=0.025, rely=0.18, relwidth=0.95, relheight=0.77
        )
        button_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        button_frame.place(
            relx=0.0333, rely=0.8714, relwidth=0.9333, relheight=0.0857
        )
        self.ai_button = ctk.CTkButton(
            button_frame,
            text=self.language_manager.get("crash_log.ai_analysis"),
            command=lambda: threading.Thread(target=self.analyze_with_ai).start(),
            font=("Segoe UI", 20, "bold"),
        )
        self.ai_button.place(
            relx=0.32145, rely=0.15, relwidth=0.3571, relheight=0.7
        )
        if not online:
            self.ai_button.configure(state="disabled")

    def _text(self, key: str) -> str:
        return self.language_manager.get(key)

    def _restore_titlebar_color(self, event: Any = None) -> None:
        self.header_color_setter(self, self.titlebar_color)

    def cancel_analyze(self) -> None:
        self.ai_button.configure(
            state="disabled", text=self._text("main.status.finalizing")
        )
        if self.thread is not None:
            self.kill_thread(self.thread)
            self.thread = None

    def analyze_with_ai(self) -> None:
        self.logger("Начало AI анализа лога краша")
        self.ai_button.configure(
            text=self._text("crash_log.cancel_analysis"), command=self.cancel_analyze
        )
        self.thread = threading.Thread(target=self.analyze)
        self.thread.start()
        self.thread.join()
        if self.thread:
            self.logger("AI анализ завершён, показ результата")
            self.set_solution_text()
        self.ai_button.configure(
            text=self._text("crash_log.ai_analysis"),
            command=lambda: threading.Thread(target=self.analyze_with_ai).start(),
            state="normal",
        )

    def set_solution_text(self) -> None:
        self.solution_textbox.configure(state="normal")
        self.solution_textbox.delete("0.0", "end")
        self.solution_textbox.insert("0.0", self.message)
        self.solution_textbox.configure(state="disabled")

    def set_log_text(self, text: str) -> None:
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("0.0", "end")
        self.log_textbox.insert("0.0", text)
        self.log_textbox.configure(state="disabled")

    def analyze(self) -> None:
        language = "ru" if self.language == "be" else self.language
        system_prompt = (
            "Вы — эксперт-помощник по анализу логов Minecraft"
            "Ваша задача:\n"
            "1) Кратко (одним предложением) описать причину краша.\n"
            "2) Предложить только те решения, которые напрямую связаны с выявленной причиной.\n\n"
            "Формат ответа:\n"
            "[Причина краша одним предложением]\n"
            "1. Первое конкретное решение\n"
            "2. Второе конкретное решение\n"
            "Правила:\n"
            f"- Ты отвечаешь исключительно только на языке {language}.\n"
            "- Решения должны быть написаны для обычного пользователя Minecraft-лаунчера.\n"
            "- Максимальное количество решений 3.\n"
            "- Не включайте общие или универсальные советы, если они не связаны напрямую с выявленной причиной.\n"
            "- НЕ пишите вступительные фразы, приветствия или объяснения. Начинайте сразу с причины.\n\n"
            "Если на входе не лог Minecraft, ответьте точно словом None (без кавычек, markdown и любого дополнительного текста).\n"
            "Если в логах недостаточно информации для чёткого определения причины, ответьте точно словом None (без кавычек, markdown и любого дополнительного текста)."
        )
        try:
            self.message = self.analyzer.get_response([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self.log_textbox.get("0.0", "end")},
            ])
            if self.message == "None":
                raise ValueError("No actionable crash analysis was returned")
        except Exception:
            self.exception_handler(*sys.exc_info())
            self.message = self._text("messages.texts.error.failed_analyze")

    def open(self) -> None:
        self.deiconify()
        self.geometry(f"+{self.center_window(self, 600, 700)}")
