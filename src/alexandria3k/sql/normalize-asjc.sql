/*
 * Alexandria3k Crossref bibliographic metadata processing
 * Copyright (C) 2022  Diomidis Spinellis
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
 * Normalize ASJC general fields
 */

-- Create general fields table
DROP TABLE IF EXISTS asjc_general_fields;
CREATE TABLE asjc_general_fields AS 
  SELECT Cast(id AS INTEGER) AS id, Replace(field, "General ", "") AS name
  FROM asjc
  WHERE id % 100 == 0
;

-- Set the asjc asjc_general_fields field
UPDATE asjc SET general_field_id=(
  SELECT id FROM asjc_general_fields
  WHERE asjc_general_fields.id = (asjc.id / 100) * 100
);
