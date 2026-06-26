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

        self.log_textbox = ctk.CTkTextbox(
            self,
            font=("Segoe UI", 13),
            state="disabled",
            wrap="word",
        )
        self.log_textbox.place(relx=0.0333, rely=0.1286, relwidth=0.9333, relheight=0.35)

        self.solution_frame = ctk.CTkFrame(
            self,
            border_width=2,
            corner_radius=12,
        )
        self.solution_frame.place(relx=0.0333, rely=0.5, relwidth=0.9333, relheight=0.35)
        
        solution_title = ctk.CTkLabel(
            self.solution_frame,
            text=language_manager.get("crash_log.solution_title", "🔍 Решение проблемы"),
            font=("Segoe UI", 18, "bold"),
            fg_color="transparent",
            anchor="w",
        )
        solution_title.place(relx=0.025, rely=0.02, relwidth=0.95, relheight=0.12)
        
        self.solution_textbox = ctk.CTkTextbox(
            self.solution_frame,
            font=("Segoe UI", 13),
            state="disabled",
            wrap="word",
            corner_radius=8,
            activate_scrollbars=True,
        )
        self.solution_textbox.place(
            relx=0.025,
            rely=0.18,
            relwidth=0.95,
            relheight=0.77,
        )

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
        hPyT.title_bar_color.set(self, GuiOptions.fg_color)

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
            self.set_solution_text()
        self.ai_button.configure(text=language_manager.get("crash_log.ai_analysis"),
                                 command=lambda: threading.Thread(target=self.analyze_with_ai).start(),
                                 state="normal")
    
    def set_solution_text(self):
        self.solution_textbox.configure(state="normal")
        self.solution_textbox.delete("0.0", "end")
        self.solution_textbox.insert("0.0", self.message)
        self.solution_textbox.configure(state="disabled")
        
    def set_log_text(self, text: str):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("0.0", "end")
        self.log_textbox.insert("0.0", text)
        self.log_textbox.configure(state="disabled")

    def analyze(self) -> str:
        try:
            system_prompt = (
                f"Вы — эксперт-помощник по анализу логов Minecraft"
                "Ваша задача:\n"
                "1) Кратко (одним предложением) описать причину краша.\n"
                "2) Предложить только те решения, которые напрямую связаны с выявленной причиной.\n\n"
                "Формат ответа:\n"
                "[Причина краша одним предложением]\n"
                "1. Первое конкретное решение\n"
                "2. Второе конкретное решение\n"
                "Правила:\n"
                f"- Ты отвечаешь исключительно только на языке {'ru' if language == 'be' else language}.\n"
                "- Решения должны быть написаны для обычного пользователя Minecraft-лаунчера.\n"
                "- Максимальное количество решений 3.\n"
                "- Не включайте общие или универсальные советы, если они не связаны напрямую с выявленной причиной.\n"
                "- НЕ пишите вступительные фразы, приветствия или объяснения. Начинайте сразу с причины.\n\n"
                "Если на входе не лог Minecraft, ответьте точно словом None (без кавычек, markdown и любого дополнительного текста).\n"
                "Если в логах недостаточно информации для чёткого определения причины, ответьте точно словом None (без кавычек, markdown и любого дополнительного текста)."
            )
            
            self.message = LogAnalyzer().get_response([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self.log_textbox.get("0.0", "end")}
            ])
            if self.message == "None":
                raise Exception("None")
        except Exception as e:
            excepthook(*sys.exc_info())
            self.message = language_manager.get("messages.texts.error.failed_analyze")

    def open(self):
        self.deiconify()
        self.geometry(f"+{center(self, 600, 700)}")


class LogAnalyzer:
    def __init__(self):
        self.POLLINATIONS_URL = "https://text.pollinations.ai/"
        self.MCLO_URL = "https://api.mclo.gs/1/analyse"
        self.headers = {
            "User-Agent": LauncherConfig.USER_AGENT,
            "Content-Type": "application/json"
        }


    def _try_mclo(self, messages: list, timeout: int) -> str | Exception:
        payload = {
            "content": messages[1]["content"]
        }
        try:
            resp = requests.post(self.MCLO_URL, json=payload, headers=self.headers, timeout=timeout)
            resp.raise_for_status()
            return "\n".join(
                solution["message"]
                for problem in resp.json()["analysis"]["problems"]
                for solution in problem["solutions"]
            )
        except Exception as e:
            excepthook(*sys.exc_info())
            return e
        
        
    def _try_pollinations(self, messages: list, timeout: int) -> str | Exception:
        payload = {
            "messages": messages
        }

        try:
            resp = requests.post(self.POLLINATIONS_URL, json=payload, headers=self.headers, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            excepthook(*sys.exc_info())
            return e

    def get_response(self, messages: list, timeout: int = 30) -> str | Exception:
        response1 = self._try_pollinations(messages, timeout)
        if not isinstance(response1, Exception) and response1 != "None":
            log("Получен ответ от Pollinations API", source="crash")
            return response1
        
        response2 = self._try_mclo(messages, timeout)
        if not isinstance(response2, Exception) and response2:
            log("Получен ответ от Mclo API", source="crash")
            return response2
        log("Все API не сработали", level="ERROR", source="crash")
        return response2