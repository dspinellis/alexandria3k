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
 * Normalize open access journals table
 * This could be done with a single command, but then it would fail as
 * a whole if some columns were missing.
 * In the current form individual statements can be skipped if needed.
 */

-- Remove dash from ISSNs
UPDATE open_access_journals SET issn_print = REPLACE(issn_print, '-', '');
UPDATE open_access_journals SET issn_eprint = REPLACE(issn_eprint, '-', '');
UPDATE open_access_journals SET continues = REPLACE(REPLACE(continues, '-', ''), ' ', '');
UPDATE open_access_journals SET continued_by = REPLACE(REPLACE(continued_by, '-', ''), ' ', '');

-- Make fields to be an integer
UPDATE open_access_journals SET oaj_start = null WHERE oaj_start = '';
UPDATE open_access_journals SET oaj_start = Cast(oaj_start AS integer);

UPDATE open_access_journals SET sub_pub_weeks = null WHERE sub_pub_weeks = '';
UPDATE open_access_journals SET sub_pub_weeks = Cast(sub_pub_weeks AS integer);

UPDATE open_access_journals SET article_records_number = null WHERE article_records_number = '';
UPDATE open_access_journals SET article_records_number = Cast(article_records_number AS integer);

UPDATE open_access_journals SET author_copyright = 1 WHERE author_copyright='Yes';
UPDATE open_access_journals SET author_copyright = 0 WHERE author_copyright='No';
UPDATE open_access_journals SET author_copyright = null WHERE author_copyright='';

UPDATE open_access_journals SET apc = 1 WHERE apc='Yes';
UPDATE open_access_journals SET apc = 0 WHERE apc='No';
UPDATE open_access_journals SET apc = null WHERE apc='';

UPDATE open_access_journals SET other_fees = 1 WHERE other_fees='Yes';
UPDATE open_access_journals SET other_fees = 0 WHERE other_fees='No';
UPDATE open_access_journals SET other_fees = null WHERE other_fees='';

UPDATE open_access_journals SET orcid_in_metadata = 1 WHERE orcid_in_metadata = 'Yes';
UPDATE open_access_journals SET orcid_in_metadata = 0 WHERE orcid_in_metadata = 'No';
UPDATE open_access_journals SET orcid_in_metadata = null WHERE orcid_in_metadata = '';

UPDATE open_access_journals SET i4oc_compliance = 1 WHERE i4oc_compliance = 'Yes';
UPDATE open_access_journals SET i4oc_compliance = 0 WHERE i4oc_compliance = 'No';
UPDATE open_access_journals SET i4oc_compliance = null WHERE i4oc_compliance = '';

UPDATE open_access_journals SET doaj_oa_compliance = 1 WHERE doaj_oa_compliance = 'Yes';
UPDATE open_access_journals SET doaj_oa_compliance = 0 WHERE doaj_oa_compliance = 'No';
UPDATE open_access_journals SET doaj_oa_compliance = null WHERE doaj_oa_compliance = '';
