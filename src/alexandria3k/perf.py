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
"""Maintain and output time performance values."""

import time

from alexandria3k import debug

PERF_FLAG = "perf"

# By default use perf_counter() rather than process_time() to also
# take into account I/O time
counter = time.perf_counter
start = counter()
previous = start


def log(message):
    """Print the specified performance message and times.
    This will output the relative elapsed time from the previous
    output, the absolute time since the program's start, and
    the specified message.

    To obtain performance output messages you need to enable the
    corresponding debug flag.

    .. code-block:: python

        debug.enable_flags(["perf"]).

    :param message: Message to output
    :type message: str
    """
    if not debug.enabled(PERF_FLAG):
        return
    now = counter()
    relative = now - start
    # pylint: disable-next=invalid-name,global-statement
    global previous
    delta = now - previous
    debug.log(PERF_FLAG, f"{relative:10} {delta:10} {message}")
    previous = now
