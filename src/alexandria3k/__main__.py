#!/usr/bin/env python3
#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2022-2025  Diomidis Spinellis
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""Command-line interface"""

import argparse
import csv
import importlib
import os
import random
import shutil
import sys
import textwrap
import traceback

from alexandria3k.common import Alexandria3kError, program_version
from alexandria3k import debug
from alexandria3k.file_cache import FileCache
from alexandria3k import perf

DESCRIPTION = "a3k: Relational interface to publication metadata"


random.seed("alexandria3k")


def module_get_attribute(name, attribute_name):
    """Return the attribute of the module with the specified name."""
    module = importlib.import_module(f"alexandria3k.{name}")
    return getattr(module, attribute_name)


def module_name(facility):
    """Given the user-visible name of a facility (e.g. funder-names)
    return the corresponding name of the module (e.g funder_names)."""
    return facility.replace("-", "_")


def class_name(facility):
    """Given the user-visible name of a facility (e.g. funder-names)
    return the corresponding name of the class (e.g FunderNames)."""
    components = facility.split("-")
    # Capitalize the first letter of each component and join them together.
    return "".join(x.title() for x in components)


def facility_modules(facility):
    """Return a list with the module names of the available facilities"""
    main_dir = os.path.dirname(os.path.realpath(__file__))
    python_files = os.listdir(f"{main_dir}/{facility}")
    # Remove trailing .py
    return [os.path.splitext(f)[0] for f in python_files if f.endswith(".py")]


def facility_names(facility):
    """Return a list with the names of the available facilities.
    (data_source or process)"""
    # Replace _ with -
    return [s.replace("_", "-") for s in facility_modules(facility)]


def get_data_source_instance(args):
    """Return a data source instance based on the specified user arguments."""
    facility = args.data_name
    module = module_name(f"data_sources.{facility}")

    default_source = module_get_attribute(module, "DEFAULT_SOURCE")
    data_location = args.data_location or default_source
    if not data_location:
        raise Alexandria3kError(
            f"The data source {facility} requires the specification of a data location"
        )

    # The sampling expression defaults to True or it can be
    # given via the CI. One can manipulate the sampling function
    # by using a variable called data as the input argument
    # of the lambda function to access the input of the callable.
    # (e.g. For USPTO sampling the input of the callable is a tuple)
    # pylint: disable-next=eval-used
    sample = eval(f"lambda data: {args.sample}")

    class_ = module_get_attribute(module, class_name(facility))
    return class_(data_location, sample, args.attach_databases)


def download(args):
    """Download data using the specified data source."""
    args.validate_args(args)
    data_source_instance = get_data_source_instance(args)
    extra_args = args.extra_args if args.extra_args is not None else []
    data_source_instance.download(
        database=args.database,
        sql_query=args.sql_query,
        data_location=args.data_location,
        *extra_args,
    )
    perf.log(f"Data downloaded and saved to {args.data_location}")


def validate_args(args):
    """Validate that both database and sql_query are either both provided or both omitted."""
    if bool(args.database) != bool(args.sql_query):
        raise argparse.ArgumentTypeError(
            "Both --database and --sql-query must be provided together or not at all."
        )
    return args


def add_subcommand_download(subparsers):
    """Add the arguments of the download subcommand."""
    parser = subparsers.add_parser(
        "download", help="Download data using the specified data source."
    )
    parser.set_defaults(func=download)
    parser.add_argument(
        "-d", "--database", help="File path of the database to use", nargs="?"
    )
    parser.add_argument(
        "data_name",
        choices=facility_names("data_sources"),
        help="Name of the data source to use",
    )
    parser.add_argument(
        "--sql-query",
        type=str,
        help="SQL query to retrieve the data for downloading",
    )
    parser.add_argument(
        "data_location",
        type=str,
        help="File or directory path to save the downloaded data",
    )
    parser.add_argument(
        "--extra_args",
        nargs="*",
        help="Additional arguments for the data source (e.g. URL, key, file path)",
    )
    parser.add_argument(
        "-s",
        "--sample",
        default="True",
        type=str,
        help="Python expression to sample the data (e.g. random.random() < 0.0002). "
        + "The expression can also use a variable named data whose value is documented "
        + "in the constructor API of each data source.",
    )
    parser.add_argument(
        "-a",
        "--attach-databases",
        nargs="+",
        type=str,
        help="Databases to attach for the row selection expression",
    )
    # Add a custom validation function to the parser
    parser.set_defaults(validate_args=validate_args)


def populate(args):
    """Populate the specified database from the specified data source."""

    data_source_instance = get_data_source_instance(args)

    if args.row_selection and args.row_selection_file:
        raise argparse.ArgumentTypeError(
            "Only one of the --row-selection or --row-selection-file options can be specified."
        )

    if args.row_selection_file:
        with open(args.row_selection_file, encoding="utf-8") as file:
            args.row_selection = file.read()

    data_source_instance.populate(
        args.database,
        args.columns,
        args.row_selection,
    )
    perf.log("Table population")


def add_subcommand_populate(subparsers):
    """Add the arguments of the populate subcommand."""
    parser = subparsers.add_parser(
        "populate",
        help="Populate an SQLite database from the specified data source.",
    )
    parser.set_defaults(func=populate)
    parser.add_argument(
        "database", help="File path of the database to populate"
    )
    parser.add_argument(
        "data_name",
        choices=facility_names("data_sources"),
        help="Name of the data source to use",
    )
    parser.add_argument(
        "data_location",
        nargs="?",
        type=str,
        help="Path or URL of the source's data",
    )
    parser.add_argument(
        "-a",
        "--attach-databases",
        nargs="+",
        type=str,
        help="Databases to attach for the row selection expression",
    )
    parser.add_argument(
        "-c",
        "--columns",
        nargs="+",
        type=str,
        help="Columns to populate using table.column or table.*",
    )
    parser.add_argument(
        "-R",
        "--row-selection-file",
        type=str,
        help="File containing SQL expression that selects the populated rows",
    )
    parser.add_argument(
        "-r",
        "--row-selection",
        type=str,
        help="SQL expression that selects the populated rows",
    )
    parser.add_argument(
        "-s",
        "--sample",
        default="True",
        type=str,
        help="Python expression to sample the data (e.g. random.random() < 0.0002). "
        + "The expression can also use a variable named data whose value is documented "
        + "in the constructor API of each data source.",
    )


def process(args):
    """Populate the specified database from the specified data source."""

    module = module_name(f"processes.{args.process}")
    process_function = module_get_attribute(module, "process")
    process_function(args.database)
    perf.log(f"Process {args.process} execution")


def add_subcommand_process(subparsers):
    """Add the arguments of the process subcommand."""
    parser = subparsers.add_parser(
        "process", help="Run a processing step on the specified database."
    )
    parser.set_defaults(func=process)
    parser.add_argument(
        "database", help="file path of the database to run the process on"
    )
    parser.add_argument(
        "process",
        choices=facility_names("processes"),
        help=(
            "Name of the process to perform;"
            "see the data processing operations in the Alexandria3k "
            "Python user API documentation for more details"
        ),
    )


def add_subcommand_help(top_parser, subparsers):
    """Add the arguments of the populate subcommand."""

    def top_level_help(_args):
        """Display top-level help."""
        top_parser.print_help()

    parser = subparsers.add_parser("help", help="Show top-level help message.")
    parser.set_defaults(func=top_level_help)


def query(args):
    """Query the specified data source."""
    data_source_instance = get_data_source_instance(args)

    if args.query and args.query_file:
        raise argparse.ArgumentTypeError(
            "Only one of the --query or --query-file options can be specified."
        )

    if args.query_file:
        with open(args.query_file, encoding="utf-8") as file:
            args.query = file.read()

    if args.output:
        # pylint: disable-next=R1732
        csv_file = open(
            args.output, "w", newline="", encoding=args.output_encoding
        )
    else:
        sys.stdout.reconfigure(encoding=args.output_encoding)
        csv_file = sys.stdout

    csv_writer = csv.writer(csv_file, delimiter=args.field_separator)
    for rec in data_source_instance.query(args.query, args.partition):
        if args.header:
            csv_writer.writerow(data_source_instance.get_query_column_names())
            args.header = False
        csv_writer.writerow(rec)
    csv_file.close()
    debug.log("files-read", f"{FileCache.file_reads} files read")
    perf.log("Query execution")


def add_subcommand_query(subparsers):
    """Add the arguments of the populate subcommand."""
    parser = subparsers.add_parser(
        "query",
        help=(
            "Run a query directly on a data source. The query's results can "
            "be sent to the standard output (default), to a specified file, "
            "or to populate a table in an attached database."
        ),
    )
    parser.set_defaults(func=query)
    parser.add_argument(
        "data_name",
        choices=facility_names("data_sources"),
        help="Name of the data source to use",
    )
    parser.add_argument(
        "data_location", nargs="?", help="Path or URL of the source's data"
    )

    parser.add_argument(
        "-a",
        "--attach-databases",
        nargs="+",
        type=str,
        help="Databases to attach making them available to the query",
    )
    parser.add_argument(
        "-E",
        "--output-encoding",
        type=str,
        default="utf-8",
        help="Query output character encoding (use utf-8-sig for Excel)",
    )
    parser.add_argument(
        "-F",
        "--field-separator",
        type=str,
        default=",",
        help="Character to use for separating query output fields",
    )
    parser.add_argument(
        "-H",
        "--header",
        action="store_true",
        help="Include a header in the query output",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file for query results",
    )
    parser.add_argument(
        "-P",
        "--partition",
        action="store_true",
        # pylint: disable-next=line-too-long
        help="Run the query over partitioned data slices. (Warning: arguments are run per partition.)",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-Q",
        "--query-file",
        type=str,
        help="File containing query to run on the virtual tables",
    )
    group.add_argument(
        "-q", "--query", type=str, help="Query to run on the virtual tables"
    )
    parser.add_argument(
        "-s",
        "--sample",
        default="True",
        type=str,
        help="Python expression to sample the data (e.g. random.random() < 0.0002). "
        + "The expression can also use a variable named data whose value is documented "
        + "in the constructor API of each data source.",
    )


def get_tables(name):
    """Return a list of the schema of the tables in the specified module"""
    tables = module_get_attribute(name, "tables")
    return [table.table_schema() for table in tables]


def list_facility_schema(facility, args):
    """Print the specified facility (data_sources or processes) data
    schema."""
    if args.facility:
        result = get_tables(f"{facility}.{module_name(args.facility)}")
    else:
        # All modules, but each table only once
        result = set()
        for module in facility_modules(facility):
            result.update(get_tables(f"{facility}.{module}"))
    for table_schema in result:
        print(table_schema)


def add_subcommand_list_complete_schema(subparsers):
    """Add the list-complete-schema subcommand."""

    def list_complete_schema(args):
        """Print the specified data source schema (or all)."""
        args.facility = None
        list_facility_schema("data_sources", args)
        list_facility_schema("processes", args)

    parser = subparsers.add_parser(
        "list-complete-schema",
        help="List all data source and process schemas.",
    )
    parser.set_defaults(func=list_complete_schema)


def add_subcommand_list_source_schema(subparsers):
    """Add the list-source-schema subcommand."""

    def list_source_schema(args):
        """Print the specified data source schema (or all)."""
        list_facility_schema("data_sources", args)

    parser = subparsers.add_parser(
        "list-source-schema",
        help="List all data source schemas (default) or the specified one.",
    )
    parser.set_defaults(func=list_source_schema)
    parser.add_argument(
        "facility", nargs="?", choices=facility_names("data_sources")
    )


def add_subcommand_list_process_schema(subparsers):
    """Add the list-process-schema subcommand."""

    def list_process_schema(args):
        """Print the specified process schema (or all)."""
        list_facility_schema("processes", args)

    parser = subparsers.add_parser(
        "list-process-schema",
        help="List the schema of all processes (default) or of the specified one.",
    )
    parser.set_defaults(func=list_process_schema)
    parser.add_argument(
        "facility", nargs="?", choices=facility_names("processes")
    )


def list_facility_description(facility, show_default):
    """Print the specified facility (data_sources or processes) description
    When show_default is True, also add the data source's default data
    source."""
    indent = max(len(name) for name in facility_names(facility)) + 3

    width = shutil.get_terminal_size().columns if os.isatty(1) else 1e9
    for name in facility_names(facility):
        module = module_name(f"{facility}.{name}")
        description = module_get_attribute(module, "__doc__")
        text = description
        if show_default:
            default = module_get_attribute(module, "DEFAULT_SOURCE") or "None"
            text += f"; default data source: {default}"
        wrapped = textwrap.fill(
            text,
            width=width,
            initial_indent=f"{name}:" + (" " * (indent - len(name) - 1)),
            subsequent_indent=" " * indent,
        )
        print(wrapped)


def add_subcommand_list_processes(subparsers):
    """Add the list-processes subcommand."""

    def list_processes(_args):
        """Print a description of available processes."""
        list_facility_description("processes", False)

    parser = subparsers.add_parser(
        "list-processes", help="List available data processes."
    )
    parser.set_defaults(func=list_processes)


def add_subcommand_list_sources(subparsers):
    """Add the list-sources subcommand."""

    def list_sources(_args):
        """Print a description of available data sources."""
        list_facility_description("data_sources", True)

    parser = subparsers.add_parser(
        "list-sources", help="List available data sources"
    )
    parser.set_defaults(func=list_sources)


def add_subcommand_version(subparsers):
    """Add the version subcommand."""

    def show_version(_args):
        """Display program version and exit"""
        print(f"a3k version {program_version()}")

    parser = subparsers.add_parser("version", help="Report program version")
    parser.set_defaults(func=show_version)


def get_cli_parser():
    """Return a CLI parser (used by main() and sphinx-argparse)"""

    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument(
        "-d",
        "--debug",
        nargs=1,
        type=str,
        default=[],
        # NOTE: Keep in sync with list in debug.py
        # Exceptions:
        # stderr does not work as a Debug API flag (use Debug.set_output)
        # progress_bar is an undocumented CLI --debug option (use --progress)
        help="""Output debuggging information according to the comma-separated arguments.
    files-read: Counts of Crossref data files read;
    link: Record linking operations;
    sql: Executed SQL statements;
    perf: Performance timings;
    populated-counts: Counts of the populated database;
    populated-data: Data of the populated database;
    populated-reports: Query results from the populated database;
    sorted-tables: Topologically ordered Crossref query tables;
    stacktrace: Produce a stack trace when an error occurs;
    stderr: Log to standard error;
""",
    )
    parser.add_argument(
        "-p",
        "--progress",
        action="store_true",
        help="Show a progress bar (where available)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Report program version and exit",
    )

    # Add sub-commands
    subparsers = parser.add_subparsers(
        dest="command", help="Name of the a3k operation to perform."
    )
    add_subcommand_help(parser, subparsers)
    add_subcommand_populate(subparsers)
    add_subcommand_process(subparsers)
    add_subcommand_query(subparsers)
    add_subcommand_list_processes(subparsers)
    add_subcommand_list_complete_schema(subparsers)
    add_subcommand_list_source_schema(subparsers)
    add_subcommand_list_process_schema(subparsers)
    add_subcommand_list_sources(subparsers)
    add_subcommand_version(subparsers)
    add_subcommand_download(subparsers)
    return parser


def error_raising_main():
    """Program entry point. May raise Alexandria3kError."""
    parser = get_cli_parser()
    args = parser.parse_args()

    # Setup debug logging and performance monitoring
    if args.debug:
        debug.set_flags(args.debug[0].split(","))
    perf.log("Start")

    if args.version:
        print(f"a3k version {program_version()}")
        sys.exit(0)

    if args.progress:
        debug.set_output(sys.stderr)
        debug.set_flags(["progress_bar"])

    # Handle subcommands
    if args.command is not None:
        args.func(args)
    else:
        parser.error("No subcommand provided")

    debug.log("files-read", f"{FileCache.file_reads} files read")

    return 0


def main():
    """Program entry point that catches API's exceptions to print
    more helpful message."""
    try:
        error_raising_main()
    except Alexandria3kError as message:
        if debug.enabled("stacktrace"):
            traceback.print_stack()
        print(f"Error: {message}", file=sys.stderr)
        print("Terminating program execution.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
