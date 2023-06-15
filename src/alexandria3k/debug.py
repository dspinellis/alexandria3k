#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2022-2023  Diomidis Spinellis
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
Maintain debug state and output enabled messages.

Use example:

.. code-block:: python

    import debug

    debug.set_flags(["parsing", "time"])
    debug.log("flag_name", "Some message")
    if debug.enable("flag_name") ...
"""

import sys


enabled_flags = set()

# Output: by default stdout, but can be set
# pylint: disable-next=invalid-name
output = sys.stdout


def set_output(output_file):
    """
    Direct output to the specified output target.

    :param output_file: File object on which output the debug messages,
        e.g. `sys.stderr`.
    :type output_file: file object
    """
    # pylint: disable-next=global-statement,invalid-name
    global output
    output = output_file


def get_output():
    """Return output target"""
    return output


# NOTE: Keep in sync with list in __main__.py
def set_flags(flags):
    """
    Enable the specified debug flags.
    The following flags are supported:

    * exception: Raise an exception when an error occurs;
    * files-read: Counts of Crossref data files read;
    * link: Record linking operations;
    * sql: Executed SQL statements;
    * perf: Performance timings;
    * progress: Report population progress;
    * sorted-tables: Topologically ordered Crossref query tables;
    * stderr: Log to standard error;

    :param flags: Flags to enable.
    :type flags: list
    """
    for i in flags:
        enabled_flags.add(i)


def enabled(flag):
    """
    Check if the specified flag is enabled.

    :param flag: Flag to check.
    :type flag: str

    :return: True if the specified flag is enabled.
    :rtype: bool
    """
    return flag in enabled_flags


def log(flag, message):
    """
    Output the specified message if the corresponding flag is enabled.

    :param flag: Flag that controls the message output.
    :type flag: str

    :param message: Message to output.
    :type message: str
    """
    if flag in enabled_flags:
        print(message, file=output, flush=True)
