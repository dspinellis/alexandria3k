#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2025 Panagiotis-Alexios Spanakis
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
"""
Provides:
  --print-completion <bash|zsh|tcsh>
and dynamic completions for:
  - data_name (populate, query, download)
  - process (process subcommand)
  - facility positional arguments (list-source-schema, list-process-schema)
  - file / path arguments (--query-file, --row-selection-file,
                           --output, data_location, --attach-databases)
"""
import argparse
import sys
from typing import Any, Optional

try:
    import shtab  # type: ignore
except ImportError:  # pragma: no cover
    shtab = None

from alexandria3k.facilities import facility_names


class _MissingCompletionAction(argparse.Action):
    """Fallback action when shtab isn't installed."""

    def __call__(self, parser, namespace, values, option_string=None):
        print(
            "Install alexandria3k[completion] (adds 'shtab') for completion support.",
            file=sys.stderr,
        )
        parser.exit(1)


def _iter_subparsers(root_parser: argparse.ArgumentParser):
    """Yield (name, parser) for each subparser in *root_parser*.

    Accesses protected attributes of argparse objects; this is intentional
    and safe for building completion metadata.
    """
    for action in root_parser._actions:  # pylint: disable=protected-access
        if isinstance(
            action,
            argparse._SubParsersAction,  # pylint: disable=protected-access
        ):  # pylint: disable=protected-access
            for sp_name, sp in action.choices.items():
                yield sp_name, sp


def _attach_positional_completions(
    parser: argparse.ArgumentParser,
) -> None:  # pylint: disable=protected-access
    data_source_names = facility_names("data_sources")
    process_names = facility_names("processes")
    for sp_name, sp in _iter_subparsers(parser):
        for action in sp._actions:  # pylint: disable=protected-access
            if (
                sp_name in {"populate", "query", "download"}
                and action.dest == "data_name"
            ):
                action.complete = {"choices": data_source_names}
            if sp_name == "process" and action.dest == "process":
                action.complete = {"choices": process_names}
            if sp_name == "list-source-schema" and action.dest == "facility":
                action.complete = {"choices": data_source_names}
            if sp_name == "list-process-schema" and action.dest == "facility":
                action.complete = {"choices": process_names}


def _attach_file_option_completions(
    parser: argparse.ArgumentParser,
) -> None:  # pylint: disable=protected-access
    file_option_dests = {"row_selection_file", "query_file", "output"}
    for _, sp in _iter_subparsers(parser):
        for action in sp._actions:  # pylint: disable=protected-access
            if action.dest in file_option_dests:
                action.complete = shtab.FILE


def _attach_data_location_completions(
    parser: argparse.ArgumentParser,
) -> None:  # pylint: disable=protected-access
    for sp_name, sp in _iter_subparsers(parser):
        if sp_name in {"populate", "query", "download"}:
            for action in sp._actions:  # pylint: disable=protected-access
                if action.dest == "data_location":
                    action.complete = (
                        shtab.FILE
                    )  # If mostly dirs, change to shtab.DIR


def _attach_attach_databases_completions(
    parser: argparse.ArgumentParser,
) -> None:  # pylint: disable=protected-access
    for _sp_name, sp in _iter_subparsers(parser):
        for action in sp._actions:  # pylint: disable=protected-access
            if action.dest == "attach_databases":
                action.complete = shtab.FILE


def _attach_dynamic_completions(parser: argparse.ArgumentParser) -> None:
    """Attach project-specific completion metadata to parser actions.

    This function delegates to smaller helpers to keep complexity low for
    linting and readability.
    """
    _attach_positional_completions(parser)
    _attach_file_option_completions(parser)
    _attach_data_location_completions(parser)
    _attach_attach_databases_completions(parser)


def add_completion_support(
    parser: argparse.ArgumentParser, subparsers: Optional[Any] = None
) -> argparse.ArgumentParser:
    """
    Add (or stub) shell completion support to the top-level parser.
    Also attach dynamic completions if shtab is installed.
    """
    if shtab:
        shtab.add_argument_to(parser)  # Adds --print-completion
        if subparsers is not None and hasattr(subparsers, "choices"):

            data_source_names = facility_names("data_sources")
            process_names = facility_names("processes")
            file_like_dests = {
                "row_selection_file",
                "query_file",
                "output",
                "data_location",
                "attach_databases",
            }
            for sp_name, sp in subparsers.choices.items():  # type: ignore[attr-defined]
                for action in sp._actions:  # pylint: disable=protected-access
                    if (
                        sp_name in {"populate", "query", "download"}
                        and action.dest == "data_name"
                    ):
                        action.complete = {"choices": data_source_names}
                    elif sp_name == "process" and action.dest == "process":
                        action.complete = {"choices": process_names}
                    elif (
                        sp_name == "list-source-schema"
                        and action.dest == "facility"
                    ):
                        action.complete = {"choices": data_source_names}
                    elif (
                        sp_name == "list-process-schema"
                        and action.dest == "facility"
                    ):
                        action.complete = {"choices": process_names}
                    elif action.dest in file_like_dests:
                        action.complete = shtab.FILE
        else:
            _attach_dynamic_completions(parser)
    else:
        parser.add_argument(
            "--print-completion",
            choices=["bash", "zsh", "tcsh"],
            action=_MissingCompletionAction,
            help="print shell completion script (install alexandria3k[completion])",
        )
    return parser
