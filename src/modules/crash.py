class CrashLogWindow(ctk.CTkToplevel):
    def __init__(self):
        super().__init__(root)
        
        self.withdraw()
        
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.title(language_manager.get("crash_log.title"))
        self.geometry(f"{crash_x}x{crash_y}")
        self.resizable(False, False)
        self.thread = None
        self.message = None
        self.transient(root)
        self.bind("<Map>", self._restore_titlebar_color)
        hPyT.maximize_minimize_button.hide(self)

        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.place(relx=0.0333, rely=0.0286, relwidth=0.9333, relheight=0.1143)

        raw_logo = Image.open("png/GUI/bug.png")
        logo_ctk_image = ctk.CTkImage(light_image=raw_logo, size=(32, 32))
        logo_label = ctk.CTkLabel(top_frame, image=logo_ctk_image, fg_color="transparent", text_color=user_color)
        logo_label.place(relx=0.0, relwidth=0.0571, relheight=0.64)

        title_label = ctk.CTkLabel(
            top_frame,
            text=language_manager.get("crash_log.error_log"),
            font=get_dynamic_font("Segoe UI", 25, "bold"),
            fg_color="transparent",
            anchor="w",
            text_color=user_color
        )
        title_label.place(relx=0.0714, relwidth=0.9286, relheight=0.60)

        separator = ctk.CTkFrame(self, height=2, fg_color="white")
        separator.place(relx=0.0333, rely=0.1143, relwidth=0.9333, relheight=0.0029)

        self.log_textbox = ctk.CTkTextbox(
            self,
            font=get_dynamic_font("Segoe UI", 13),
            state="disabled",
            wrap="word",
            text_color=user_color
        )
        self.log_textbox.place(relx=0.0333, rely=0.1286, relwidth=0.9333, relheight=0.7143)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.place(relx=0.0333, rely=0.8714, relwidth=0.9333, relheight=0.0857)

        self.ai_button = ctk.CTkButton(
            button_frame,
            text=language_manager.get("crash_log.ai_analysis"),
            command=lambda: threading.Thread(target=self.analyze_with_ai).start(),
            hover_color=lighten_dominant_5,
            fg_color=lighten_dominant_10,
            font=get_dynamic_font("Segoe UI", 20, "bold"),
            text_color=user_color
        )
        self.ai_button.place(relx=0.32145, rely=0.15, relwidth=0.3571, relheight=0.7)
        if not IS_INTERNET:
            self.ai_button.configure(state="disabled")
        
    def _restore_titlebar_color(self, event=None):
        hPyT.title_bar_color.set(self, dominant_color)
        hPyT.title_bar_text_color.set(self, "#000000" if user_color == "black" else "#FFFFFF")
    
    def cancel_analyze(self):
        self.ai_button.configure(state="disabled", text=language_manager.get("main.status.finalizing"))
        kill_thread(self.thread)
        self.thread = None
    
    def analyze_with_ai(self):
        self.ai_button.configure(text=language_manager.get("crash_log.cancel_analysis"), command=self.cancel_analyze)
        self.thread = threading.Thread(target=self.analyze)
        self.thread.start()
        self.thread.join()
        if self.thread:
            new_message(
                title=language_manager.get("messages.titles.info"),
                message=self.message,
                icon="info",
                option_1=language_manager.get("messages.answers.ok")
            )
        self.ai_button.configure(text=language_manager.get("crash_log.ai_analysis"), command=lambda: threading.Thread(target=self.analyze_with_ai).start(), state="normal")
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
        self.geometry(f"+{center(self, crash_x, crash_y)}")
        


class FreeGPTClient:
    def __init__(self):
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        self.POLLINATIONS_ENDPOINT = "https://text.pollinations.ai/openai"

    @staticmethod
    def generate_signature(timestamp: int, text: str, secret: str = "") -> str:
        message = f"{timestamp}:{text}:{secret}"
        return hashlib.sha256(message.encode()).hexdigest()

    def _try_free2gpt(self, messages: list, timeout: int) -> str:
        url = "https://chat10.free2gpt.xyz/api/generate"
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Referer": "https://chat10.free2gpt.xyz/",
            "Origin": "https://chat10.free2gpt.xyz"
        }

        timestamp = int(time() * 1000)
        payload = {
            "messages": messages,
            "time": timestamp,
            "pass": None,
            "sign": self.generate_signature(timestamp, messages[-1]["content"])
        }


        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            return response.text

        except Exception as e:
            excepthook(*sys.exc_info())
            return [e.__class__.__name__]

    def _try_pollinations_ai(self, messages: list, timeout: int) -> str:
        headers = {
            "User-Agent": self.USER_AGENT,
            "Content-Type": "application/json",
            "Referer": "https://pollinations.ai"
        }

        payload = {
            "messages": messages,
            "model": "openai",
            "stream": False
        }

        try:
            response = requests.post(
                self.POLLINATIONS_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=timeout
            )

            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                return message.get("content", "")

        except Exception as e:
            excepthook(*sys.exc_info())
            return [e.__class__.__name__]
    
    def get_response(
            self,
            messages: list,
            timeout: int = 30,
    ) -> str:

        response1 = self._try_free2gpt(messages, timeout)
        if not isinstance(response1, list):
            return response1

        response2 = self._try_pollinations_ai(messages, timeout)
        if not isinstance(response2, list):
            return response2

        return [None, [response1[0], response2[0]]]