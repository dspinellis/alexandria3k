-- Create table linking works to single ISSN

CREATE TABLE rolap.works_issn AS
  SELECT id, doi, page,
    Coalesce(issn_print, issn_electronic) AS issn, published_year
  FROM works
  WHERE issn is not null;
