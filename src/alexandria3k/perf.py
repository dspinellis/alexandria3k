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
"""Output performance values"""

import time

import debug

PERF_FLAG = "perf"


class Perf(object):
    """Maintain and output time performance values.
    Use:
    p = Perf()
    p.enable()
    expensive_task()
    p.print("Finished expensive task")
    another_expensive_task()
    p.print("Finished another expensive task")
    """

    # Make this a singleton
    # See https://www.geeksforgeeks.org/singleton-pattern-in-python-a-complete-guide/
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(Perf, cls).__new__(cls)
            self = cls.instance
            # By default use perf_counter() rather than process_time() to also
            # take into account I/O time
            self.counter = time.perf_counter
            self.start = self.counter()
            self.previous = self.start

        return cls.instance

    def print(self, message):
        """Print the specified performance figure timestamp.
        To enable this call debug.enable_flags(["perf"]).
        """
        if not debug.enabled(PERF_FLAG):
            return
        now = self.counter()
        relative = now - self.start
        delta = now - self.previous
        debug.print(PERF_FLAG, f"{relative:10} Δ={delta:10} {message}")
        self.previous = now
