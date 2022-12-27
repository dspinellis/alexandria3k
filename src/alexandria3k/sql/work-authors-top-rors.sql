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
 * Map work authors to their top organizations
 */

DROP TABLE IF EXISTS work_authors_top_rors;

CREATE TABLE work_authors_top_rors AS
  WITH RECURSIVE

  -- Obtain from relationships a table of ROR parents
  ror_parents AS (
    SELECT ror_relationships.ror_id, parent.id AS ror_parent_id
    FROM research_organizations AS parent
    INNER JOIN ror_relationships
      ON parent.ror_path = ror_relationships.ror_path
        AND ror_relationships.type = 'Parent'
  ),

  -- Add parents of higher generations
  work_authors_parent_rors(ror_id, work_author_id, generation) AS (
    SELECT ror_id, work_author_id, 0 FROM work_authors_rors
    UNION
    SELECT ror_parents.ror_parent_id, work_author_id, generation + 1
    FROM work_authors_parent_rors
    INNER JOIN ror_parents
      ON work_authors_parent_rors.ror_id = ror_parents.ror_id
  ),

  -- Group by author and number by generation to obtain oldest generation
  ordered_parents AS (
    SELECT ror_id, work_author_id,
      Row_number() OVER(PARTITION BY work_author_id ORDER BY generation DESC)
        AS row
    FROM work_authors_parent_rors
  )

  SELECT ror_id, work_author_id FROM ordered_parents WHERE row = 1;

-- Rename new table into work_authors_rors, keeping the original version
DROP TABLE IF EXISTS work_authors_direct_rors;
ALTER TABLE work_authors_rors RENAME TO work_authors_direct_rors;
ALTER TABLE work_authors_top_rors RENAME TO work_authors_rors;
