from os.path import realpath
from os import startfile

from tablewrapper import TableWrapper

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
    Button
)
from textual.containers import Container, VerticalScroll
import pandas as pd


class Sidebar(Container):
    pass


class TApp(App):
    CSS_PATH = "style.css"
    tree_path = "./"
    filter_column = None
    all_none = False

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
                with TabPane("Editor", id="editor"):
                    self.editor_input = Input(
                        placeholder="Editor work in progress", id="editor", disabled=True
                    )
                    self.editor_input.styles.min_height = 10
                    yield self.editor_input
                with TabPane("Preview", id="preview"):
                    with Container(classes="horizontal preview"):
                        self.previous_button = Button("<<", id="previous", classes="preview-buttons")
                        yield self.previous_button
                        self.preview_input = Input(placeholder="0", id="preview-selector")
                        yield self.preview_input
                        self.next_button = Button(">>", id="next", classes="preview-buttons")
                        yield self.next_button
                    self.subject_input = Input(placeholder="Subject", id="subject")
                    yield self.subject_input
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
                            self.filter_select = Select(options=(), name="filter", classes="filter", id="filter")
                            yield self.filter_select
                            self.filter_input = Input(placeholder="Filter", classes="filter")
                            yield self.filter_input
            with Container(classes="horizontal bottom", id="bottom_container"):
                self.email_select = Select(options=(), name="email", prompt="Email", id="email")
                yield self.email_select
                self.send_all_button = Button("Send All", id="send_all", classes="send-buttons")
                yield self.send_all_button
                self.send_preview_button = Button("Send Preview", id="send_preview", classes="send-buttons")
                yield self.send_preview_button
            yield Footer()

    def on_mount(self):
        self.bind("q", "quit", description="Quit")
        self.bind("o", "toggle_sidebar", description="Open File")

    def action_switch_tab(self, tab_id: str):
        self.tabs.active = tab_id

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected):
        self.datatable.toggle_hide_row(self.datatable.get_by_key(event.row_key))

    @on(Select.Changed, "#filter")
    def select_changed(self, event: Select.Changed) -> None:
        if event.value is not None:
            if self.filter_column is not None:
                self.datatable.style_column(self.filter_column, style=None)
            self.filter_column = self.datatable.column_list[self.datatable.header.index(event.value)]
            self.datatable.style_column(self.filter_column, style=f"blue")
        # self.datatable.filter(self.filter_select.value, self.filter_input.value)

    @on(Input.Submitted, "#filter")
    def input_submitted(self, event: Input.Submitted) -> None:
        self.datatable.filter(self.filter_select.value, self.filter_input.value)

    @on(TabbedContent.TabActivated)
    def tab_activated(self, event: TabbedContent.TabActivated) -> None:
        # if event.tab.id == "preview":
        #     self.preview.update(self.editor_input.value)
        # elif event.tab.id == "editor":
        #     self.editor_input.focus()
        ...

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
        startfile(realpath(self.tree_path))

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
                self.preview.update(f.read())
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
            if mail_option := self.find_mail_option(self.datatable.header):
                self.email_select.value = mail_option
        else:
            return
        self.action_toggle_sidebar()

    def find_mail_option(self, options: list):
        mail_list = ["mail"," adress", "address"]
        for option in options:
            for mail in mail_list:
                if mail in option.lower():
                    return option


if __name__ == "__main__":
    app = TApp()
    app.run()
