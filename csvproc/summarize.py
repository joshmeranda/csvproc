from __future__ import annotations

import csv
import dataclasses
import dateutil.parser
import enum
import typing
import json


@enum.unique
class ColumnType(enum.IntEnum):
    """Describes the data type of a columns values.

    Each enum field's assigned value represents the data type parsing
    precedence when determine the type of a record value.
    """
    UNKNOWN = 0

    INT = 3

    FLOAT = 5

    DATETIME = 7

    STRING = 9

    @staticmethod
    def determine_type(value: str) -> ColumnType:
        """Determine the data type of the column"""
        try:
            dateutil.parser.parse(value)
            return ColumnType.DATETIME
        except ValueError:
            pass

        try:
            float(value)
            return ColumnType.FLOAT
        except ValueError:
            pass

        try:
            int(value)
            return ColumnType.INT
        except ValueError:
            pass

        return ColumnType.STRING


class SummaryFormat(enum.Enum):
    """Options for summary out put formats,"""

    DEFAULT = enum.auto()

    # same as default but with a complete description of the data.
    VERBOSE = enum.auto()

    # all data is output as json.
    JSON = enum.auto()

    # same as JSON but cleanly indented
    JSON_PRETTY = enum.auto()


@dataclasses.dataclass(frozen=True)
class ColumnSummary:
    field_name: str
    type: ColumnType
    choices: typing.Set[str]
    optional: bool = False
    boolean: bool = False
    enum: bool = False

    def __init__(self, field_name: str, values: typing.Set[str]):
        """A simple summary class describing a single column in a csv file.

        :param field_name: The field title of the column.
        :param values: All the values under the column.
        """
        object.__setattr__(self, "field_name", field_name)
        object.__setattr__(self, "choices", values)

        if len(values) == 2:
            object.__setattr__(self, "boolean", True)

        column_type: ColumnType = ColumnType.UNKNOWN
        for val in values:
            if not val:
                object.__setattr__(self, "optional", True)

            val_type: ColumnType = ColumnType.determine_type(val)

            if val_type > column_type:
                column_type = val_type

            if val_type == ColumnType.STRING:
                break

        object.__setattr__(self, "type", column_type)


class SummaryEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, CsvSummary):
            return {
                "columns": [self.default(column) for column in obj.columns],
                "record_count": obj.record_count
            }

        if isinstance(obj, ColumnSummary):
            return {
                "field_name": obj.field_name,
                "type": obj.type,
                "choices": list(obj.choices),
                "optional": obj.optional,
                "boolean": obj.boolean,
                "enum": obj.enum
            }

        return json.JSONEncoder.default(self, obj)


@dataclasses.dataclass(frozen=True)
class CsvSummary:
    path: str
    columns: typing.List[ColumnSummary]
    record_count: int

    def __init__(self, *, file: typing.TextIO = None, path: str = None):
        """A basic summary describing a csv file's structure and contents.

        One or both 'file' and 'path' must be provided; however, if both are
        given, the path is ignored.

        :param file: The file like object to use for parsing the csv.
        :param path: The path of the file to use for parsing the csv.
        """
        if file is not None:
            self.__summarize(file)
            object.__setattr__(self, "path", file.name)
        elif path is not None:
            with open(path) as file:
                self.__summarize(file)
            object.__setattr__(self, "path", path)
        else:
            raise Exception("One of 'file' or 'path' must be specified")

    def __summarize(self, file: typing.TextIO):
        """Parse and initialize summary values.
        todo: validate csv date
            not empty
            has headers

        :param file: The source file like object for the csv reader.
        """
        reader = csv.DictReader(file)
        columns: typing.Dict[str, typing.Set[str]] = {field_name: set() for field_name in reader.fieldnames}

        object.__setattr__(self, "record_count", reader.line_num)

        for row in reader:
            for key, val in row.items():
                if val:
                    columns[key].add(val)

        object.__setattr__(self, "columns", list())

        for field_name, values in columns.items():
            summary = ColumnSummary(field_name, values)
            self.columns.append(summary)

    def write_summary(self, file: typing.TextIO, summary_format: SummaryFormat,
                      encoder: typing.Type[json.JSONEncoder] = SummaryEncoder):
        """Write a text representation of the csv summary.

        :param file: The open file like object to which the summary is to be written.
        :param summary_format: The format of the output.
        :param encoder: The json encoder to use if writing summary as JSON, ignored otherwise.
        """

        if summary_format == SummaryFormat.JSON:
            summary: str = json.dumps(self, cls=encoder)

        elif summary_format == SummaryFormat.JSON_PRETTY:
            summary: str = json.dumps(self, cls=encoder, indent=2)

        elif summary_format == SummaryFormat.DEFAULT or summary_format == SummaryFormat.VERBOSE:
            summary: str = (f"=== {self.path} ====\n"
                            f"Record Count: {self.record_count}\n\n")
            for column in self.columns:
                summary += (f"Field Name: {column.field_name}\n"
                            f"Type: {column.type.value}\n")

                if summary_format == SummaryFormat.VERBOSE or column.optional:
                    summary += f"Optional: {column.optional}\n"

                if summary_format == SummaryFormat.VERBOSE or column.boolean:
                    summary += f"Boolean: {column.boolean}\n"

                if summary_format == SummaryFormat.VERBOSE or column.enum:
                    summary += f"Enum: {column.enum} {column.choices}\n"

                summary += "\n"

        else:
            raise Exception("Unsupported summary format")

        file.write(summary)
