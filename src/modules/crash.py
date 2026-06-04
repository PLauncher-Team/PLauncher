from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *


class CrashLogWindow(ctk.CTkToplevel):
    def __init__(self):
        super().__init__(root)

        self.withdraw()

        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.title(language_manager.get("crash_log.title"))
        self.geometry(f"{600}x{700}")
        self.resizable(False, False)
        self.thread = None
        self.message = None
        self.transient(root)
        self.bind("<Map>", self._restore_titlebar_color)
        hPyT.maximize_minimize_button.hide(self)

        top_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        top_frame.place(relx=0.0333, rely=0.0286, relwidth=0.9333, relheight=0.1143)

        raw_logo = PIL.Image.open("png/GUI/bug.png")
        logo_ctk_image = ctk.CTkImage(light_image=raw_logo, size=(32, 32))
        logo_label = ctk.CTkLabel(top_frame, image=logo_ctk_image, fg_color="transparent")
        logo_label.place(relx=0.0, relwidth=0.0571, relheight=0.64)

        title_label = ctk.CTkLabel(
            top_frame,
            text=language_manager.get("crash_log.error_log"),
            font=("Segoe UI", 25, "bold"),
            fg_color="transparent",
            anchor="w",
        )
        title_label.place(relx=0.0714, relwidth=0.9286, relheight=0.60)

        separator = ctk.CTkFrame(self, height=2, fg_color="white", border_width=0)
        separator.place(relx=0.0333, rely=0.1143, relwidth=0.9333, relheight=0.0029)

        self.log_textbox = ctk.CTkTextbox(
            self,
            font=("Segoe UI", 13),
            state="disabled",
            wrap="word",
        )
        self.log_textbox.place(relx=0.0333, rely=0.1286, relwidth=0.9333, relheight=0.7143)

        button_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        button_frame.place(relx=0.0333, rely=0.8714, relwidth=0.9333, relheight=0.0857)

        self.ai_button = ctk.CTkButton(
            button_frame,
            text=language_manager.get("crash_log.ai_analysis"),
            command=lambda: threading.Thread(target=self.analyze_with_ai).start(),
            font=("Segoe UI", 20, "bold"),
        )
        self.ai_button.place(relx=0.32145, rely=0.15, relwidth=0.3571, relheight=0.7)
        if not LauncherConfig.IS_INTERNET:
            self.ai_button.configure(state="disabled")

    def _restore_titlebar_color(self, event=None):
        hPyT.title_bar_color.set(self, GuiOptions.hover_color)

    def cancel_analyze(self):
        self.ai_button.configure(state="disabled", text=language_manager.get("main.status.finalizing"))
        kill_thread(self.thread)
        self.thread = None

    def analyze_with_ai(self):
        log("Начало AI анализа лога краша", source="crash")
        self.ai_button.configure(text=language_manager.get("crash_log.cancel_analysis"), command=self.cancel_analyze)
        self.thread = threading.Thread(target=self.analyze)
        self.thread.start()
        self.thread.join()
        if self.thread:
            log("AI анализ завершён, показ результата", source="crash")
            new_message(
                title=language_manager.get("messages.titles.info"),
                message=self.message,
                icon="info",
                option_1=language_manager.get("messages.answers.ok")
            )
        self.ai_button.configure(text=language_manager.get("crash_log.ai_analysis"),
                                 command=lambda: threading.Thread(target=self.analyze_with_ai).start(),
                                 state="normal")
        self.withdraw()

    def set_log_text(self, text: str):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("0.0", "end")
        self.log_textbox.insert("0.0", text)
        self.log_textbox.configure(state="disabled")

    def analyze(self) -> str:
        try:
            self.message = FreeGPTClient().get_response([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": self.log_textbox.get("0.0", "end")}
            ])
            if self.message == "None":
                self.message = [None, ["None"]]
            if isinstance(self.message, list):
                raise Exception("\n".join(self.message[1]))
        except Exception as e:
            excepthook(*sys.exc_info())
            self.message = language_manager.get("messages.texts.error.failed_analyze") + str(e)

    def open(self):
        self.deiconify()
        self.geometry(f"+{center(self, 600, 700)}")


class FreeGPTClient:
    def __init__(self):
        self.TEACH_ANYTHING_URL = "https://www.teach-anything.com/api/generate"

    def _try_teach_anything(self, messages: list, timeout: int) -> str | list:
        headers = {
            "User-Agent": LauncherConfig.USER_AGENT,
            "Content-Type": "application/json",
            "Origin": "https://www.teach-anything.com",
            "Referer": "https://www.teach-anything.com/"
        }

        def format_prompt(msgs: list) -> str:
            parts = []
            for m in msgs:
                parts.append(f"[{m['role'].upper()}] {m['content']}")
            return "\n".join(parts)

        payload = {
            "prompt": format_prompt(messages)
        }
        try:
            resp = requests.post(self.TEACH_ANYTHING_URL, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except Exception:
            excepthook(*sys.exc_info())
            return [Exception.__name__]

    def get_response(self, messages: list, timeout: int = 30) -> str | list:
        response = self._try_teach_anything(messages, timeout)
        if not isinstance(response, list):
            log("Получен ответ от Teach Anything API", source="crash")
            return response
        log("Все AI API не сработали", level="ERROR", source="crash")
        return [None, [response]]