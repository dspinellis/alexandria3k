-- Create table linking works to a single journal id

CREATE TABLE rolap.works_journal_id AS
  SELECT id, doi, page, journals_issns.journal_id, published_year
  FROM works
  INNER JOIN journals_issns ON
    Coalesce(issn_print, issn_electronic) = journals_issns.issn;
