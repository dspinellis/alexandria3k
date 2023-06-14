-- Create a table of works that are available as open access

CREATE INDEX IF NOT EXISTS open_access_journals_issn_print_idx
  ON open_access_journals(issn_print);

CREATE INDEX IF NOT EXISTS open_access_journals_issn_eprint_idx
  ON open_access_journals(issn_eprint);

CREATE INDEX IF NOT EXISTS works_issn_print_idx on works(issn_print);
CREATE INDEX IF NOT EXISTS works_issn_electronic_idx on works(issn_electronic);

CREATE TABLE rolap.oa_works AS
  SELECT works.id AS work_id, doaj_url FROM works
  INNER JOIN open_access_journals ON
    open_access_journals.issn_print = works.issn_print
    OR
    open_access_journals.issn_eprint = works.issn_electronic
  WHERE works.published_year >= oaj_start;
