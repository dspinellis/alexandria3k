#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2022  Diomidis Spinellis
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
"""Maintain debug state and output enabled messages

Use:
import debug
debug.set_flags(["parsing", "time"])
debug.log("flag_name", "Some message")
if debug.enable("flag_name") ...
"""

import sys


flags = set()

# Output: by default stdout, but can be set
# pylint: disable-next=invalid-name
output = sys.stdout


def set_output(output_arg):
    """Direct output to the specified output target"""
    # pylint: disable-next=global-statement,invalid-name
    global output
    output = output_arg


def get_output():
    """Return output target"""
    return output


def set_flags(flags_arg):
    """Enable the specified debug flags"""
    for i in flags_arg:
        flags.add(i)


def enabled(flag):
    """Return true if the specified flag is enabled"""
    return flag in flags


def log(flag, message):
    """Print the specified message if the corresponding flag is enabled"""
    if flag in flags:
        print(message, file=output, flush=True)
