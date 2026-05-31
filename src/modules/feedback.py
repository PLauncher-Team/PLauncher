from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import *

class FeedbackApp(ctk.CTkToplevel):
    def __init__(self):
        """
        Initialize feedback window UI and components
        """
        super().__init__(root)

        self.withdraw()

        self.title(language_manager.get("feedback.title"))
        self.geometry(f"{500}x{400}")
        self.resizable(False, False)
        self.grab_set()
        self.bind("<Map>", self._restore_titlebar_color)
        self.transient(root)

        hPyT.window_frame.center_relative(root, self)

        self.email_label = ctk.CTkLabel(
            self,
            text=language_manager.get("feedback.email"),
            font=("Segoe UI", 13)
        )
        self.email_label.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.05)

        self.email_entry = ctk.CTkEntry(
            self,
            font=("Segoe UI", 13),
            border_width=0
        )
        self.email_entry.place(relx=0.02, rely=0.07, relwidth=0.96, relheight=0.07)

        self.subject_label = ctk.CTkLabel(
            self,
            text=language_manager.get("feedback.subject"),
            font=("Segoe UI", 13)
        )
        self.subject_label.place(relx=0.02, rely=0.16, relwidth=0.96, relheight=0.05)

        self.subject_entry = ctk.CTkEntry(
            self,
            font=("Segoe UI", 13),
            border_width=0
        )
        self.subject_entry.place(relx=0.02, rely=0.21, relwidth=0.96, relheight=0.07)

        self.desc_label = ctk.CTkLabel(
            self,
            text=language_manager.get("feedback.description"),
            font=("Segoe UI", 13)
        )
        self.desc_label.place(relx=0.02, rely=0.30, relwidth=0.96, relheight=0.05)

        self.desc_text = ctk.CTkTextbox(self)
        self.desc_text.place(relx=0.02, rely=0.35, relwidth=0.96, relheight=0.45)

        self.send_button = ctk.CTkButton(
            self,
            text=language_manager.get("feedback.send"),
            command=lambda: threading.Thread(target=self.on_send_click).start(),
            font=("Segoe UI", 13, "bold")
        )
        self.send_button.place(relx=0.40, rely=0.82, relwidth=0.20, relheight=0.06)

        self.deiconify()

    def _restore_titlebar_color(self, event=None):
        """
        Restore custom title bar color on window map event
        """
        hPyT.title_bar_color.set(self, GuiOptions.hover_color)


    def fetch_dynamic_field_ids(self) -> dict[str, str]:
        """Fetch dynamic Google Form field IDs directly from the HTML text using regex.
    
        :return: Dictionary mapping labels to field entry IDs
        """
        response = requests.get("https://docs.google.com/forms/d/e/1FAIpQLScHheNuuIixaus6D_2iNRMNIMrbJWmiq-Rc7XKNf5lBo0f3NA/viewform", timeout=5)
        response.raise_for_status()
    
        match = re.search(
            r"var FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.+?\])\s*;",
            response.text,
            re.DOTALL,
        )
        if not match:
            raise ValueError("Could not find FB_PUBLIC_LOAD_DATA_ in the page source.")
    
        form_data = json.loads(match.group(1))
    
        try:
            questions = form_data[1][1]
        except (IndexError, TypeError):
            return {}
    
        return {
            question[1]: f"entry.{question[4][0][0]}"
            for question in questions
            if len(question) > 4 and question[4] and question[4][0]
        }


    def send_feedback(self, subject: str, description: str, email: str = "") -> tuple[bool, str]:
        """
        Send feedback form data via HTTP POST to Google Form

        :param subject: Feedback subject
        :param description: Feedback message content
        :param email: Optional user email
        :return: Tuple of success status and error message (if any)
        """
        try:
            log(f"Sending feedback: subject='{subject}', email='{email}'", source="feedback")
            field_ids = self.fetch_dynamic_field_ids()
            payload = {
                field_ids["Email"]: email,
                field_ids["Тема "]: subject,
                field_ids["Описание проблемы / предложения"]: description,
            }
            response = requests.post("https://docs.google.com/forms/d/e/1FAIpQLScHheNuuIixaus6D_2iNRMNIMrbJWmiq-Rc7XKNf5lBo0f3NA/formResponse", data=payload, timeout=5, headers={"User-Agent": LauncherConfig.USER_AGENT})
            response.raise_for_status()
            log("Feedback sent successfully", source="feedback")
            return True, ""
        except Exception as e:
            log(f"Failed to send feedback: {e}", level="ERROR", source="feedback")
            excepthook(*sys.exc_info())
            return False, str(e)

    def on_send_click(self):
        """
        Handle 'Send' button click event. Validate input and send feedback
        """
        email = self.email_entry.get().strip()
        subject = self.subject_entry.get().strip()
        description = self.desc_text.get("0.0", "end").strip()

        if not subject or not description:
            return

        if email and not EMAIL_REGEX.match(email):
            log(f"Invalid email format: {email}", level="WARNING", source="feedback")
            ToastNotification(
                title=language_manager.get("messages.titles.error"),
                message=language_manager.get("messages.texts.error.feedback_send"),
                toast_type="error"
            )
            return
        self.send_button.configure(state="disabled")
        success, error_msg = self.send_feedback(subject=subject, description=description, email=email)

        if success:
            ToastNotification(
                title=language_manager.get("messages.titles.info"),
                message=language_manager.get("messages.texts.check.feedback_send"),
            )
            self.email_entry.delete(0, "end")
            self.subject_entry.delete(0, "end")
            self.desc_text.delete("0.0", "end")
        else:
            ToastNotification(
                title=language_manager.get("messages.titles.error"),
                message=language_manager.get("messages.texts.error.feedback_email") + error_msg,
                toast_type="error"
            )

        self.send_button.configure(state="normal")
        self.destroy()
