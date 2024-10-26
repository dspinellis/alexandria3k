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
 * Normalize ISSNs
 */

UPDATE journal_names
  SET issn_print=REPLACE(issn_print, '-', ''),
    issn_eprint=REPLACE(issn_eprint, '-', ''),
    issns_additional=REPLACE(issns_additional, '-', '');

DROP TABLE IF EXISTS journals_issns;

-- Recursively split additional ISSNs into multiple records
CREATE TABLE journals_issns AS
  WITH RECURSIVE split(journal_id, issn, rest) AS (
     SELECT id, '', issns_additional || '; ' FROM journal_names
     UNION ALL SELECT
       journal_id,
       Substr(rest, 0, Instr(rest, '; ')),
       Substr(rest, Instr(rest, '; ')+2)
     FROM split WHERE rest != ''
  )
  SELECT journal_id, issn, 'A' AS issn_type FROM split
    WHERE issn != '';

-- Finish populating the journals_issns table
INSERT INTO journals_issns
  SELECT id, issn_print, 'P' FROM journal_names WHERE issn_print != '';

INSERT INTO journals_issns
  SELECT id, issn_eprint, 'E' FROM journal_names WHERE issn_eprint != '';

CREATE INDEX journals_issns_issn_idx ON journals_issns(issn);
CREATE INDEX journals_issns_id_idx ON journals_issns(journal_id);
