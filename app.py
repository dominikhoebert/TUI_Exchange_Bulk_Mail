import os
from dataclasses import dataclass
from os.path import realpath
import re
import configparser
from datetime import datetime

from textual.reactive import reactive
from textual.screen import ModalScreen

from tablewrapper import TableWrapper, DataRow

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    DataTable,
    Input,
    Select,
    TabbedContent,
    TabPane,
    Markdown,
    DirectoryTree,
    Static,
    Button, Label,
    OptionList
)
from textual.containers import Container, VerticalScroll, Horizontal
from textual.validation import Number, Regex
import pandas as pd
from exchangelib import DELEGATE, Account, Credentials, Message, HTMLBody
import markdown
from markdown.extensions.tables import TableExtension
from xhtml2pdf import pisa
from textual_textarea import TextArea

help_text = """
# Usage
1. Press the `o`-Key (or select "Open File" in the Footer at the bottom) to open files.
2. Select a Table File (XLSX, CSV).
    - if no usable file can be found, press "Open Folder" to open the current directory in the file explorer
        move your files to this directory and try again
3. Filter the table
    - Clicking a row to hide/unhide it
    - Clicking the "All/None" Button to hide/unhide all rows
    - Selecting a column in the dropdown and typing in the input field to filter the table
        (e.g. select "Name" and type "John" to only show rows with "John" in the "Name" column)
        (numbers can be filtered with "<" or ">" e.g. "<100" to only show numbers smaller than 100)
4. Press the `o`-Key again to open a template file (MD, TXT).
    - The first line of the template can be a subject (e.g. "subject: Hello World")
    - Move between the different recipients with the `<<` and `>>` buttons (or type in the input field)
    - 0 is the empty template which will not be sent
5. Put in your credentials in the "Settings" tab (full Email Address and Password)
6. If not automatically selected, select the column with the email addresses in the dropdown
7. Press the "Send All" Button to send all emails
   - A confirmation dialog will appear
* Press the "Send Preview" Button to send the current preview to your email address
* Press the "Export All" Button to export all emails to a PDF file
* Press the "Export Preview" Button to export the current preview to a PDF file

### Editor

The editor supports markdown and has a list with all columns of the table.
You can insert a column by clicking on it in the list.
Column Names are surrounded by double square brackets (e.g. [[Name]]).
CTRL+S to save the template.

"""


class Sidebar(Container):
    pass


@dataclass
class Email:
    address: str
    subject: str
    message: str


def find_mail_option(options: list):
    mail_list = ["mail", " adress", "address"]
    for option in options:
        for mail in mail_list:
            if mail in option.lower():
                return option


class BulkMail(App, inherit_bindings=False):
    CSS_PATH = "style.css"
    tree_path = "./"
    filter_column = None
    all_none = False
    template = "## Preview"
    preview_number = 0
    email_credential = None
    password_credential = None
    config = configparser.ConfigParser()

    def compose(self) -> ComposeResult:
        yield Header()
        self.sidebar = Sidebar(classes="-hidden")
        with self.sidebar:
            yield Static("Open File")
            with Container():
                yield DirectoryTree(self.tree_path, id="tree")
            yield Static("Table Formats: XLSX, CSV")
            yield Static("Template Formats: MD, TXT")
            yield Button("Open Folder", id="open")
        self.tabs = TabbedContent()
        with Container():
            with self.tabs:
                with TabPane("Preview", id="preview"):
                    with Container(classes="horizontal preview"):
                        self.previous_button = Button("<<", id="previous", classes="preview-buttons")
                        yield self.previous_button
                        self.validator = Number(minimum=0, maximum=0)
                        self.preview_input = Input(placeholder="0", id="preview-selector", validators=[self.validator])
                        yield self.preview_input
                        self.next_button = Button(">>", id="next", classes="preview-buttons")
                        yield self.next_button
                    self.subject_input = Input(placeholder="Subject", id="subject")
                    yield self.subject_input
                    with VerticalScroll(id="preview_scroll", classes=""):
                        self.preview = Markdown("## Preview")
                        yield self.preview
                with TabPane("Table", id="table"):
                    with VerticalScroll(id="table_scroll", classes=""):
                        self.datatable = TableWrapper()
                        self.datatable.cursor_foreground_priority = False
                        self.datatable.zebra_stripes = True
                        self.datatable.cursor_type = "row"
                        yield self.datatable
                        with Container(classes="horizontal", id="filter_container"):
                            self.all_none_button = Button("All/None", id="all_none")
                            yield self.all_none_button
                            self.filter_select = Select(options=(), name="filter", classes="filter", id="filter-select")
                            yield self.filter_select
                            self.filter_input = Input(placeholder="Filter", classes="filter", id="filter")
                            yield self.filter_input
                with TabPane("Editor", id="editor"):
                    self.fields = OptionList()
                    yield self.fields
                    self.editor_input = TextArea(language="markdown", theme="github-dark")
                    yield self.editor_input
                with TabPane("Settings", id="settings"):
                    yield Label("Exchange Credentials")
                    self.email_validator = Regex(regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
                                                 failure_description="Invalid Email")
                    self.email_credentials_input = Input(placeholder="Email", id="email_credentials",
                                                         classes="settings", validators=[self.email_validator])
                    yield self.email_credentials_input
                    self.password_credentials_input = Input(placeholder="Password", id="password_credentials",
                                                            classes="settings", password=True)
                    yield self.password_credentials_input
                    self.save_button = Button("Save", id="save", classes="settings")
                    yield self.save_button
                with TabPane("Help", id="help"):
                    yield Markdown(help_text)
            with Container(classes="horizontal bottom", id="bottom_container"):
                self.email_select = Select(options=(), name="email", prompt="Email", id="email")
                yield self.email_select
                self.send_all_button = Button("Send All", id="send_all", classes="send-buttons")
                yield self.send_all_button
                self.send_preview_button = Button("Send Preview", id="send_preview", classes="send-buttons")
                yield self.send_preview_button
                self.export_all_button = Button("Export All", id="export_all", classes="send-buttons")
                yield self.export_all_button
                self.export_preview_button = Button("Export Preview", id="export_preview", classes="send-buttons")
                yield self.export_preview_button
            yield Footer()
        self.load_credentials()

    class MessageScreen(ModalScreen):
        CSS_PATH = "MessageScreen.css"
        message = reactive("")

        def compose(self) -> ComposeResult:
            yield Container(
                Static(self.message, classes="message"),
                Horizontal(
                    Button("OK", variant="success", id="ok"),
                    Button("Cancel", variant="error", id="cancel"),
                    classes="buttons"
                ),
                id="dialog",
            )

    @on(Button.Pressed, "#ok")
    def ok_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()
        self.send_all_mails()

    @on(Button.Pressed, "#cancel")
    def cancel_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()

    def load_credentials(self):
        try:
            self.config.read(".settings.ini")
            self.email_credential = self.config["credentials"]["email"]
            self.email_credentials_input.value = self.email_credential
            self.password_credential = self.config["credentials"]["password"]
            self.password_credentials_input.value = self.password_credential
        except KeyError:
            pass

    def on_mount(self):
        self.bind("q", "quit", description="Quit")
        self.bind("o", "toggle_sidebar", description="Open File")
        self.bind("d", "toggle_dark", description="Toggle Dark mode")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_switch_tab(self, tab_id: str):
        self.tabs.active = tab_id

    @on(TabbedContent.TabActivated)
    def tab_activated(self, event: TabbedContent.TabActivated):
        if event.tab.id == "editor":
            self.editor_input.focus()
        if event.tab.id == "preview":
            if self.editor_input.text != self.template:
                self.template = self.editor_input.text
                self.set_preview()

    @on(OptionList.OptionSelected)
    def option_selected(self, event: OptionList.OptionSelected):
        print(event.option.prompt)
        self.editor_input.insert_text_at_selection("[[" + str(event.option.prompt) + "]]")

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected):
        self.datatable.toggle_hide_row(self.datatable.get_by_key(event.row_key))

    @on(Select.Changed, "#filter-select")
    def select_changed(self, event: Select.Changed) -> None:
        if event.value is not None:
            if self.filter_column is not None:
                self.datatable.style_column(self.filter_column, style=None)
            self.filter_column = self.datatable.column_list[self.datatable.header.index(event.value)]
            self.datatable.style_column(self.filter_column, style=f"blue")

    @on(Input.Submitted, "#filter")
    def input_submitted(self, event: Input.Submitted) -> None:
        self.datatable.filter(self.filter_select.value, self.filter_input.value)

    def action_toggle_sidebar(self) -> None:
        sidebar = self.sidebar
        self.set_focus(None)
        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    @on(Button.Pressed, "#open")
    def open_folder(self, event: Button.Pressed) -> None:
        os.startfile(realpath(self.tree_path))  # Windows
        # os.system(f"open {realpath(self.tree_path)}")  # Mac

    @on(Button.Pressed, "#all_none")
    def all_none(self, event: Button.Pressed) -> None:
        if self.all_none:
            for row in self.datatable.row_list:
                self.datatable.hide_row(row)
        else:
            for row in self.datatable.row_list:
                self.datatable.show_row(row)
        self.all_none = not self.all_none

    @on(DirectoryTree.FileSelected)
    def file_selected(self, event: DirectoryTree.FileSelected) -> None:
        if str(event.path).endswith(".md") or str(event.path).endswith(".txt"):
            with open(event.path) as f:
                self.template = f.read()
                if self.template.startswith("subject:"):
                    self.subject_input.value = self.template.splitlines()[0].replace("subject:", "").strip()
                    self.template = "\n".join(self.template.splitlines()[1:])
            self.action_switch_tab("preview")
        elif str(event.path).endswith(".xlsx") or str(event.path).endswith(".csv"):
            if str(event.path).endswith(".xlsx"):
                df = pd.read_excel(event.path, sheet_name=0)
            elif str(event.path).endswith(".csv"):
                df = pd.read_csv(event.path)
            self.datatable.clear(columns=True)
            self.datatable.load_dataframe(df)
            self.action_switch_tab("table")
            self.filter_select.set_options(((h, h) for h in self.datatable.header))
            self.email_select.set_options(((h, h) for h in self.datatable.header))
            self.fields.clear_options()
            self.fields.add_options([h for h in self.datatable.header])
            if mail_option := find_mail_option(self.datatable.header):
                self.email_select.value = mail_option
            self.validator.maximum = len(self.datatable)
        else:
            return
        self.editor_input.text = self.template
        self.set_preview()
        self.action_toggle_sidebar()

    def set_preview(self) -> None:
        if self.preview_number == 0:
            preview_text = "*This is the empty template which will not be sent.*   \n\n"
            self.preview.update(preview_text + self.template)
        elif self.preview_number <= len(self.datatable):
            row = self.datatable[self.preview_number - 1]
            self.preview.update(self.create_message_from_template(self.template, row))

    def create_message_from_template(self, template: str, row: DataRow) -> str:
        message = template
        for key, value in zip(self.datatable.header, row.values):
            message = message.replace(f"[[{key}]]", str(value))
        if row.hidden:
            hidden_message = "*This message is excluded by filter and will not be sent. Check the table.*"
            message = hidden_message + "   \n\n" + message + "   \n\n" + hidden_message
        return message

    @on(Input.Submitted, "#preview-selector")
    def preview_submitted(self, event: Input.Submitted) -> None:
        if len(event.validation_result.failures) == 0:
            self.preview_number = int(event.value)
            self.set_preview()

    @on(Button.Pressed, "#previous")
    def previous_pressed(self, event: Button.Pressed) -> None:
        self.preview_number = self.preview_number - 1 if self.preview_number > 0 else 0
        self.preview_input.value = str(self.preview_number)
        self.set_preview()

    @on(Button.Pressed, "#next")
    def next_pressed(self, event: Button.Pressed) -> None:
        self.preview_number = self.preview_number + 1 if self.preview_number < len(self.datatable) else len(
            self.datatable)
        self.preview_input.value = str(self.preview_number)
        self.set_preview()

    @on(Button.Pressed, "#save")
    def save_pressed(self, event: Button.Pressed) -> None:
        self.save_credentials()

    @on(Input.Submitted, ".settings")
    def settings_submitted(self, event: Input.Submitted) -> None:
        self.save_credentials()

    def save_credentials(self):
        self.email_credential = self.email_credentials_input.value
        self.password_credential = self.password_credentials_input.value
        self.config["credentials"] = {"email": self.email_credential,
                                      "password": self.password_credential}
        with open(".settings.ini", "w") as configfile:
            self.config.write(configfile)
        self.notify("Credentials saved")

    @on(Button.Pressed, "#send_all")
    def send_all_pressed(self, event: Button.Pressed) -> None:
        if self.mail_pre_check():
            return
        message_screen = self.MessageScreen()
        message_screen.message = "Are you sure you want to send " + str(self.datatable.count_non_hidden()) + " emails?"
        self.push_screen(message_screen)

    def send_all_mails(self):
        self.notify("Sending " + str(self.datatable.count_non_hidden()) + " emails...")
        emails = []
        regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
        for row in self.datatable.row_list:
            if row.hidden is False:
                email_address = row[self.email_select.value]
                if re.fullmatch(regex, email_address):
                    message = self.create_message_from_template(self.template, row)
                    message = markdown.markdown(message, extensions=[TableExtension()])
                    mail = Email(address=row[self.email_select.value], subject=self.subject_input.value,
                                 message=message)
                    emails.append(mail)
                else:
                    self.notify(f"Skipped invalid Email {email_address}")
        sent_successfully = self.send_emails(emails)
        self.notify(f"{sent_successfully} emails sent successfully.\n{len(emails) - sent_successfully} emails failed.")

    @on(Button.Pressed, "#send_preview")
    def send_preview_pressed(self, event: Button.Pressed) -> None:
        if self.mail_pre_check():
            return
        self.notify("Sending Preview to " + self.email_credential + "...")
        row = self.datatable[self.preview_number - 1]
        message = self.create_message_from_template(self.template, row)
        message = markdown.markdown(message, extensions=[TableExtension()])
        mail = Email(address=self.email_credential, subject=self.subject_input.value, message=message)
        sent_sucessfully = self.send_emails([mail])
        if sent_sucessfully == 1:
            self.notify("Preview sent sucessfully!")

    def mail_pre_check(self):
        if self.email_select.value is None or self.email_select.value == "":
            self.notify("Please select an email column")
            return True
        if self.email_credential is None or self.password_credential is None:
            self.notify("Please enter credentials")
            return True
        if self.subject_input.value == "" or self.subject_input.value is None:
            self.notify("Please enter a subject")
            return True
        return False

    def send_emails(self, emails: list) -> int:
        credentials = Credentials(username=self.email_credential, password=self.password_credential)
        exchange_account = Account(
            primary_smtp_address=self.email_credential, credentials=credentials,
            autodiscover=True, access_type=DELEGATE
        )

        message_ids = []
        for email in emails:
            message = Message(
                account=exchange_account,
                folder=exchange_account.drafts,
                subject=email.subject,
                body=HTMLBody(email.message),
                to_recipients=[email.address]
            ).save()
            message_ids.append((message.id, message.changekey))

        result = exchange_account.bulk_send(ids=message_ids)
        return result.count(True)

    @on(Button.Pressed, "#export_preview")
    def export_preview_pressed(self, event: Button.Pressed) -> None:
        if self.mail_pre_check():
            return
        filename = datetime.now().strftime("%Y%m%d-%H%M_") + self.subject_input.value + ".pdf"
        if self.preview_number > 0:
            row = self.datatable[self.preview_number - 1]
            message = self.create_message_from_template(self.template, row)
            message = f"**Recipient:** *{row[self.email_select.value]}*\n\n" + message
        else:
            message = f"**Preview**\n\n" + self.template
        message = markdown.markdown(message, extensions=[TableExtension()])
        with open(filename, "w+b") as f:
            pisa_status = pisa.CreatePDF(message + "<hr>", dest=f)
        self.notify("Exported to " + filename)

    @on(Button.Pressed, "#export_all")
    def export_all_pressed(self, event: Button.Pressed) -> None:
        if self.mail_pre_check():
            return
        filename = datetime.now().strftime("%Y%m%d-%H%M_") + self.subject_input.value + ".pdf"
        messages = f"{self.datatable.count_non_hidden()}/{len(self.datatable)} Emails\n<hr>\n\n"
        for row in self.datatable.row_list:
            if row.hidden is False:
                message = self.create_message_from_template(self.template, row)
                message = f"**Recipient:** *{row[self.email_select.value]}*\n\n" + message
                messages += markdown.markdown(message, extensions=[TableExtension()]) + "\n<hr>\n\n"

        with open(filename, "w+b") as f:
            pisa_status = pisa.CreatePDF(messages, dest=f)
        self.notify(f"{self.datatable.count_non_hidden()}/{len(self.datatable)} Emails exported to {filename}")


if __name__ == "__main__":
    app = BulkMail()
    app.run()
