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

-- Create general fields table from ids ending in 00
DROP TABLE IF EXISTS asjc_general_fields;
CREATE TABLE asjc_general_fields AS
  SELECT Cast(code AS INTEGER) AS id, Replace(field, 'General ', '') AS name
  FROM asjc_import
  WHERE code % 100 == 0
;

-- Create general fields table with own-generated ids
DROP TABLE IF EXISTS asjc_subject_areas;
CREATE TABLE asjc_subject_areas AS
  SELECT row_number() OVER (ORDER BY '') AS id, name FROM (
    SELECT DISTINCT subject_area AS name FROM asjc_import
    ORDER BY subject_area
  );

-- Create asjcs table with ids to subject areas and general fields
DROP TABLE IF EXISTS asjcs;
CREATE TABLE asjcs AS
SELECT asjc_import.code AS id, field,
  asjc_subject_areas.id AS subject_area_id,
  (asjc_import.code / 100) * 100 AS general_field_id
FROM asjc_import
INNER JOIN asjc_subject_areas
  ON asjc_subject_areas.name = asjc_import.subject_area;
