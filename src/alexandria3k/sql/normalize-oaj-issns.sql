/*
 * Alexandria3k Crossref bibliographic metadata processing
 * Copyright (C) 2023  Diomidis Spinellis
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 * Normalize ISSNs
 */

UPDATE open_access_journals
  SET issn_print=REPLACE(issn_print, "-", ""),
    issn_eprint=REPLACE(issn_eprint, "-", "");
