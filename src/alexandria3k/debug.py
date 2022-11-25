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
"""Output debug info based on flags"""

import sys
import time


class Debug(object):
    """Maintain debug state and output enabled messages
    Use:
    d = Debug() # Can be used in multiple places
    d.set_flags(["parsing", "time"])
    d.print("flag_name", "Some message")
    """

    # Make this a singleton
    # See https://www.geeksforgeeks.org/singleton-pattern-in-python-a-complete-guide/
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(Debug, cls).__new__(cls)
            self = cls.instance
            self.flags = set()
            self.output = sys.stdout
        return cls.instance

    def set_output(self, output):
        """Direct output to the specified output target"""
        self.output = output

    def get_output(self):
        """Return output target"""
        return self.output

    def set_flags(self, flags):
        """Enable the specified debug flags"""
        for i in flags:
            self.flags.add(i)

    def enabled(self, flag):
        """Return true if the specified flag is enabled"""
        return flag in self.flags

    def print(self, flag, message):
        """Print the specified message if the corresponding flag is enabled"""
        if flag in self.flags:
            print(message, file=self.output, flush=True)
