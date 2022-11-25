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
debug.print("flag_name", "Some message")
if debug.enable("flag_name") ...
"""

import builtins
import sys
import time


flags = set()
output = sys.stdout


def set_output(output_arg):
    """Direct output to the specified output target"""
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


def print(flag, message):
    """Print the specified message if the corresponding flag is enabled"""
    if flag in flags:
        builtins.print(message, file=output, flush=True)
