from dataclasses import dataclass, field

from pandas import DataFrame
from rich.text import Text
from textual.widgets.data_table import ColumnKey, RowKey
from textual.coordinate import Coordinate

from textual.widgets import DataTable


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
    def header(self, headers: list, clear: bool = False):
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

    def get_by_header(self, header: str) -> DataRow:
        if header not in self.header:
            raise ValueError(f"Header {header} not found in {self.header}")
        return self.row_list[self.header.index(header)]

    def __len__(self):
        return len(self.row_list)

    def __getitem__(self, item) -> DataRow:
        if isinstance(item, int):
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
        if row.hidden:
            self.hide_row(row)
        else:
            self.show_row(row)

    def hide_row(self, row: DataRow):
        row.hidden = True
        self.style_row(row.row_index, style="red strike")

    def show_row(self, row: DataRow):
        row.hidden = False
        self.style_row(row.row_index, style=None)

    def show_hide_row(self, row: DataRow, show: bool):
        if show:
            self.show_row(row)
        else:
            self.hide_row(row)

    def filter(self, column: str, text: str):
        if column not in self.header:
            raise ValueError(f"Column {column} not found in {self.header}")
        column_key = self.column_keys[self.header.index(column)]
        if text.startswith("<") or text.startswith(">"):
            if text[1:].isnumeric():
                n = float(text[1:])
                for row in self.row_list:
                    if text[0] == "<":
                        self.show_hide_row(row, float(row.get_by_key(column_key)) < n)
                    elif text[0] == ">":
                        self.show_hide_row(row, float(row.get_by_key(column_key)) > n)
        else:
            for row in self.row_list:
                if text != str(row.get_by_key(column_key)):
                    self.hide_row(row)
                else:
                    self.show_row(row)

    def clear(self, columns: bool = False):
        super().clear(columns=columns)
        if columns:
            self.column_list = []
            self.width = None
        self.row_list = []
        return self

    def load_array(self, array: list):
        self.header = array[0]
        for row in array[1:]:
            self.add_data_rows(DataRow(row))

    def load_dataframe(self, df: DataFrame):
        self.header = df.columns
        for row in df.values:
            self.add_data_rows(DataRow(row))

    def count_non_hidden(self):
        return len([r for r in self.row_list if not r.hidden])
