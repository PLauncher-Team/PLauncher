class FeedbackApp(ctk.CTkToplevel):
    def __init__(self):
        """
        Initialize feedback window UI and components
        """
        super().__init__(root)

        self.withdraw()

        self.title(language_manager.get("feedback.title"))
        self.geometry(f"{feedback_x}x{feedback_y}")
        self.resizable(False, False)
        self.grab_set()
        self.bind("<Map>", self._restore_titlebar_color)
        self.transient(root)

        hPyT.window_frame.center_relative(root, self)

        self.email_label = ctk.CTkLabel(
            self,
            text=language_manager.get("feedback.email"),
            font=get_dynamic_font("Segoe UI", 13)
        )
        self.email_label.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.05)

        self.email_entry = ctk.CTkEntry(
            self,
            font=get_dynamic_font("Segoe UI", 13),
            border_width=0
        )
        self.email_entry.place(relx=0.02, rely=0.07, relwidth=0.96, relheight=0.07)

        self.subject_label = ctk.CTkLabel(
            self,
            text=language_manager.get("feedback.subject"),
            font=get_dynamic_font("Segoe UI", 13)
        )
        self.subject_label.place(relx=0.02, rely=0.16, relwidth=0.96, relheight=0.05)

        self.subject_entry = ctk.CTkEntry(
            self,
            font=get_dynamic_font("Segoe UI", 13),
            border_width=0
        )
        self.subject_entry.place(relx=0.02, rely=0.21, relwidth=0.96, relheight=0.07)

        self.desc_label = ctk.CTkLabel(
            self,
            text=language_manager.get("feedback.description"),
            font=get_dynamic_font("Segoe UI", 13)
        )
        self.desc_label.place(relx=0.02, rely=0.30, relwidth=0.96, relheight=0.05)

        self.desc_text = ctk.CTkTextbox(self)
        self.desc_text.place(relx=0.02, rely=0.35, relwidth=0.96, relheight=0.45)

        self.send_button = ctk.CTkButton(
            self,
            text=language_manager.get("feedback.send"),
            command=self.on_send_click,
            font=get_dynamic_font("Segoe UI", 13, "bold")
        )
        self.send_button.place(relx=0.40, rely=0.82, relwidth=0.20, relheight=0.06)

        self.deiconify()

    def _restore_titlebar_color(self, event=None):
        """
        Restore custom title bar color on window map event
        """
        hPyT.title_bar_color.set(self, color_name_to_hex(hover_color))
    
    def fetch_dynamic_field_ids(self, form_view_url: str) -> dict[str, str]:
        """
        Fetch dynamic Google Form field IDs from the HTML content

        :param form_view_url: URL to Google Form view page
        :return: Dictionary mapping labels to field entry IDs
        """
        response = requests.get(form_view_url, timeout=5)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, 'html.parser')

        script_content = next(
            (script.string for script in soup.find_all('script') if script.string and 'FB_PUBLIC_LOAD_DATA_' in script.string),
            None
        )
        match = re.search(r"var FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.+?\])\s*;", script_content, re.DOTALL)
        form_data = json.loads(match.group(1))
        questions = form_data[1][1]

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
            field_ids = self.fetch_dynamic_field_ids(FORM_VIEW_URL)
            payload = {
                field_ids[TARGET_FIELD_CONFIG["Email"]["label_in_form_data"]]: email,
                field_ids[TARGET_FIELD_CONFIG["Subject"]["label_in_form_data"]]: subject,
                field_ids[TARGET_FIELD_CONFIG["Description"]["label_in_form_data"]]: description,
            }
            response = requests.post(FORM_SUBMIT_URL, data=payload, timeout=5)
            response.raise_for_status()
            return True, ""
        except Exception as e:
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
            new_message(
                title=language_manager.get("messages.titles.error"),
                message=language_manager.get("messages.texts.error.feedback_send"),
                icon="cancel",
                option_1=language_manager.get("messages.answers.ok")
            )
            return

        self.send_button.configure(state="disabled")
        success, error_msg = self.send_feedback(subject=subject, description=description, email=email)

        if success:
            new_message(
                title=language_manager.get("messages.titles.info"),
                message=language_manager.get("messages.texts.check.feedback_send"),
                icon="info",
                option_1=language_manager.get("messages.answers.ok")
            )
            self.email_entry.delete(0, "end")
            self.subject_entry.delete(0, "end")
            self.desc_text.delete("0.0", "end")
        else:
            new_message(
                title=language_manager.get("messages.titles.error"),
                message=language_manager.get("messages.texts.error.feedback_email") + error_msg,
                icon="cancel",
                option_1=language_manager.get("messages.answers.ok")
            )

        self.send_button.configure(state="normal")
        self.destroy()
