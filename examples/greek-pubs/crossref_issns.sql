-- Map both Crossref ISSN types into one, -separated one.

CREATE TABLE rolap.crossref_issns AS

WITH all_crossref_issns AS (
  SELECT doi, upper(issn_print) AS issn FROM works
  UNION
  SELECT doi, upper(issn_electronic) AS issn FROM works
)

-- Use dash separator and remove duplicates
SELECT DISTINCT doi, issn
  FROM all_crossref_issns;
