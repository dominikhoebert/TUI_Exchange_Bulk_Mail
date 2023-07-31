from dataclasses import dataclass, field
from random import randint

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.coordinate import Coordinate
from textual.widgets import (
    Header,
    Footer,
    DataTable,
    Input,
    Select,
    TabbedContent,
    TabPane,
)
from textual.widgets.data_table import ColumnKey, RowKey


@dataclass
class DataRow:
    values: list
    header: list = field(default_factory=list)
    column_keys: list[ColumnKey] = field(default_factory=list)
    row_key: RowKey = None
    row_index: int = None
    hidden: bool = False

    def get_by_header(self, header: str):
        if header not in self.header:
            raise ValueError(f"Header {header} not found in {self.header}")
        return self.values[self.header.index(header)]

    def get_by_index(self, index: int):
        if index >= len(self.values):
            raise ValueError(f"Index {index} out of bounds for {self.values}")
        return self.values[index]

    def get_by_key(self, key: ColumnKey):
        if key not in self.column_keys:
            raise ValueError(f"Key {key} not found in {self.column_keys}")
        return self.values[self.column_keys.index(key)]

    def __getitem__(self, item):
        if item is int:
            return self.get_by_index(item)
        elif item is ColumnKey:
            return self.get_by_key(item)
        return self.get_by_header(item)

    def __len__(self):
        return len(self.values)


@dataclass()
class DataColumn:
    column_key: ColumnKey
    header: str
    column_index: int
    style: str = None


class TableWrapper(DataTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.width = None
        self.row_list = []
        self.column_list = []

    @property
    def column_keys(self):
        return [c.column_key for c in self.column_list]

    @property
    def row_keys(self):
        return [p.row_key for p in self.row_list]

    @property
    def header(self):
        return [c.header for c in self.column_list]

    @header.setter
    def header(self, headers: list):
        if self.width is not None:
            raise ValueError(f"Header already set to {self.header}")
        keys = self.add_columns(*headers)
        self.column_list = [
            DataColumn(k, h, i) for k, h, i in zip(keys, headers, range(len(headers)))
        ]
        self.width = len(self.header)

    def add_data_rows(self, row: DataRow):
        if len(row) != self.width:
            raise ValueError(
                f"Person {row} has {len(row)} values, but table has {self.width} columns"
            )
        row.row_index = len(self.row_list)
        self.row_list.append(row)
        row.column_keys = self.column_keys
        row.header = self.header
        row.row_key = self.add_row(*row.values)
        self.row_keys.append(row.row_key)

    def get_by_index(self, index: int) -> DataRow:
        if index >= len(self.row_list):
            raise ValueError(f"Index {index} out of bounds for {self.row_list}")
        return self.row_list[index]

    def get_column_by_index(self, index: int) -> DataColumn:
        if index >= len(self.column_list):
            raise ValueError(f"Index {index} out of bounds for {self.column_list}")
        return self.column_list[index]

    def get_by_key(self, key: RowKey) -> DataRow:
        if key not in self.row_keys:
            raise ValueError(f"Key {key} not found in {self.row_keys}")
        return self.row_list[self.row_keys.index(key)]

    def __len__(self):
        return len(self.row_list)

    def __getitem__(self, item) -> DataRow:
        if item is int:
            return self.get_by_index(item)
        elif item is RowKey:
            return self.get_by_key(item)
        return self.get_by_header(item)

    def style_row(self, row_index, style=None):
        row = self.get_row_at(row_index)
        for i, cell in enumerate(row):
            if style is None:
                column = self.get_column_by_index(i)
                if column.style is None:
                    self.update_cell_at(Coordinate(row_index, i), str(cell))
                else:
                    self.update_cell_at(
                        Coordinate(row_index, i), Text(str(cell), style=column.style)
                    )
            else:
                self.update_cell_at(
                    Coordinate(row_index, i), Text(str(cell), style="red strike")
                )

    def style_column(self, column: DataColumn, style=None):
        column.style = style
        for row in self.row_list:
            if row.hidden is False:
                if style is None:
                    self.update_cell_at(
                        Coordinate(row.row_index, column.column_index),
                        str(row.get_by_index(column.column_index)),
                    )
                else:
                    self.update_cell_at(
                        Coordinate(row.row_index, column.column_index),
                        Text(str(row.get_by_index(column.column_index)), style=style),
                    )

    def toggle_hide_row(self, row: DataRow):
        row.hidden = not row.hidden
        self.style_row(row.row_index, style="red strike" if row.hidden else None)

    def filter(self, column: str, text: str):
        if column not in self.header:
            raise ValueError(f"Column {column} not found in {self.header}")
        column_key = self.column_keys[self.header.index(column)]
        for row in self.row_list:
            if text != row.get_by_key(column_key):
                row.hidden = True
                self.style_row(row.row_index, style="red strike")
            else:
                row.hidden = False
                self.style_row(row.row_index, style=None)


def person_table_from_array(array: list):
    p = TableWrapper()
    p.header = array[0]
    for row in array[1:]:
        p.add_data_rows(DataRow(row))
    return p


ROWS = [
    ("lane", "swimmer", "country", "time"),
    (4, "Joseph Schooling", "Singapore", 50.39),
    (2, "Michael Phelps", "United States", 51.14),
    (5, "Chad le Clos", "South Africa", 51.14),
    (6, "László Cseh", "Hungary", 51.14),
    (3, "Li Zhuhao", "China", 51.26),
    (8, "Mehdy Metella", "France", 51.58),
    (7, "Tom Shields", "United States", 51.73),
    (1, "Aleksandr Sadovnikov", "Russia", 51.84),
    (10, "Darren Burns", "Scotland", 51.84),
]


class TApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        self.tabs = TabbedContent()
        with self.tabs:
            with TabPane("Editor", id="editor"):
                ...
            with TabPane("Table", id="table"):
                self.datatable = person_table_from_array(ROWS)
                self.datatable.cursor_foreground_priority = False
                self.datatable.zebra_stripes = True
                self.datatable.cursor_type = "row"
                yield self.datatable
                self.filter_select = Select(
                    options=((h, h) for h in self.datatable.header), name="filter"
                )
                yield self.filter_select
                self.filter_input = Input(placeholder="Filter", name="filter")
                yield self.filter_input
        yield Footer()

    def on_mount(self):
        self.bind("e", "switch_tab('editor')", description="Editor")
        self.bind("t", "switch_tab('table')", description="Table")
        self.bind("q", "quit", description="Quit")

    def action_switch_tab(self, tab_id: str):
        self.tabs.active = tab_id

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected):
        self.datatable.toggle_hide_row(self.datatable.get_by_key(event.row_key))

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.datatable.style_column(
            self.datatable.column_list[self.datatable.header.index(event.value)],
            style=f"color({randint(0, 255)})",
        )
        # self.datatable.filter(self.filter_select.value, self.filter_input.value)

    @on(Input.Submitted)
    def input_submitted(self, event: Input.Submitted) -> None:
        self.datatable.filter(self.filter_select.value, self.filter_input.value)


if __name__ == "__main__":
    app = TApp()
    app.run()
