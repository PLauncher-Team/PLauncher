class CrashLogWindow(ctk.CTkToplevel):
    def __init__(self):
        """
        Initialize the crash log window UI and setup its components.
        """
        super().__init__(root)

        self.withdraw()

        # Override window close to just hide the window
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.title(language_manager.get("crash_log.title"))
        self.geometry(f"{crash_x}x{crash_y}")
        self.resizable(False, False)
        self.thread = None
        self.message = None
        self.transient(root)
        self.bind("<Map>", self._restore_titlebar_color)
        hPyT.maximize_minimize_button.hide(self)

        # Top frame containing the logo and title
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.place(relx=0.0333, rely=0.0286, relwidth=0.9333, relheight=0.1143)

        # Load and display the bug icon logo
        raw_logo = PIL.Image.open("png/GUI/bug.png")
        logo_ctk_image = ctk.CTkImage(light_image=raw_logo, size=(32, 32))
        logo_label = ctk.CTkLabel(top_frame, image=logo_ctk_image, fg_color="transparent", text_color=user_color)
        logo_label.place(relx=0.0, relwidth=0.0571, relheight=0.64)

        # Title label for the crash log window
        title_label = ctk.CTkLabel(
            top_frame,
            text=language_manager.get("crash_log.error_log"),
            font=get_dynamic_font("Segoe UI", 25, "bold"),
            fg_color="transparent",
            anchor="w",
            text_color=user_color
        )
        title_label.place(relx=0.0714, relwidth=0.9286, relheight=0.60)

        # Separator line below the title
        separator = ctk.CTkFrame(self, height=2, fg_color="white")
        separator.place(relx=0.0333, rely=0.1143, relwidth=0.9333, relheight=0.0029)

        # Textbox to display the crash log content (readonly)
        self.log_textbox = ctk.CTkTextbox(
            self,
            font=get_dynamic_font("Segoe UI", 13),
            state="disabled",
            wrap="word",
            text_color=user_color
        )
        self.log_textbox.place(relx=0.0333, rely=0.1286, relwidth=0.9333, relheight=0.7143)

        # Frame holding buttons at the bottom
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.place(relx=0.0333, rely=0.8714, relwidth=0.9333, relheight=0.0857)

        # AI analysis button starts a background thread to analyze the log
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
        """
        Restore the title bar color and text color according to user settings.
        """
        hPyT.title_bar_color.set(self, dominant_color)
        hPyT.title_bar_text_color.set(self, "#000000" if user_color == "black" else "#FFFFFF")

    def cancel_analyze(self):
        """
        Cancel the ongoing AI analysis by disabling the button and killing the thread.
        """
        self.ai_button.configure(state="disabled", text=language_manager.get("main.status.finalizing"))
        kill_thread(self.thread)
        self.thread = None

    def analyze_with_ai(self):
        """
        Start the AI analysis process, updating button text and state accordingly.
        Shows the analysis result in a message box when done.
        """
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
        self.ai_button.configure(text=language_manager.get("crash_log.ai_analysis"),
                                 command=lambda: threading.Thread(target=self.analyze_with_ai).start(),
                                 state="normal")
        self.withdraw()

    def set_log_text(self, text: str):
        """
        Set the crash log text in the readonly textbox.

        Args:
            text (str): The text content to display in the log textbox.
        """
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("0.0", "end")
        self.log_textbox.insert("0.0", text)
        self.log_textbox.configure(state="disabled")

    def analyze(self) -> str:
        """
        Perform AI analysis on the crash log content by sending it to GPT clients.

        Returns:
            str: The response message or error information.
        """
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
        """
        Show the crash log window and center it on the screen.
        """
        self.deiconify()
        self.geometry(f"+{center(self, crash_x, crash_y)}")


class FreeGPTClient:
    def __init__(self):
        """
        Initialize the FreeGPTClient with user agent and API endpoint URLs.
        """
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        self.POLLINATIONS_ENDPOINT = "https://text.pollinations.ai/openai"
        self.TEACH_ANYTHING_URL = "https://www.teach-anything.com/api/generate"

    def _try_pollinations_ai(self, messages: list, timeout: int) -> str | list:
        """
        Attempt to get a response from Pollinations AI endpoint.

        Args:
            messages (list): List of message dicts for the conversation.
            timeout (int): Request timeout in seconds.

        Returns:
            str | list: The AI response string or a list with exception name on failure.
        """
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
            resp = requests.post(self.POLLINATIONS_ENDPOINT, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            if "choices" in data and data["choices"]:
                return data["choices"][0].get("message", {}).get("content", "")
        except Exception:
            sys.excepthook(*sys.exc_info())
            return [Exception.__name__]

    def _try_teach_anything(self, messages: list, timeout: int) -> str | list:
        """
        Attempt to get a response from Teach Anything API.

        Args:
            messages (list): List of message dicts for the conversation.
            timeout (int): Request timeout in seconds.

        Returns:
            str | list: The AI response string or a list with exception name on failure.
        """
        headers = {
            "User-Agent": self.USER_AGENT,
            "Content-Type": "application/json",
            "Origin": "https://www.teach-anything.com",
            "Referer": "https://www.teach-anything.com/"
        }
        def format_prompt(msgs: list) -> str:
            """
            Format messages into a prompt string suitable for Teach Anything API.

            Args:
                msgs (list): List of message dicts.

            Returns:
                str: Formatted prompt string.
            """
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
            sys.excepthook(*sys.exc_info())
            return [Exception.__name__]

    def get_response(self, messages: list, timeout: int = 30) -> str | list:
        """
        Get a response from AI by trying Pollinations first, then Teach Anything as fallback.

        Args:
            messages (list): List of message dicts for conversation.
            timeout (int, optional): Timeout for requests. Defaults to 30.

        Returns:
            str | list: AI response string or list with error details.
        """
        response1 = self._try_pollinations_ai(messages, timeout)
        if not isinstance(response1, list):
            return response1

        response2 = self._try_teach_anything(messages, timeout)
        if not isinstance(response2, list):
            return response2
        return [None, [response2]]
