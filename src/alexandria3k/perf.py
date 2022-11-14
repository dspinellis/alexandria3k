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


class Perf:
    """Maintain and output performance values"""

    def __init__(self, enabled, counter=time.process_time):
        # By default use perf_counter() rather than process_time() to also
        # take into account I/O time
        self.counter = counter
        self.start = counter()
        self.previous = self.start

        self.output_enabled = enabled

    def print(self, message):
        """Print the specified performance timestamp"""
        if not self.output_enabled:
            return
        now = self.counter()
        relative = now - self.start
        delta = now - self.previous
        print(f"{relative:10} Δ={delta:10} {message}")
        self.previous = now
