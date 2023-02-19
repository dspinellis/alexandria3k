-- Create a table containging the average CD5 index of all articles
-- published in each journal D. Tawfik has published in the given year
-- for that same year.

CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);

ATTACH DATABASE '../cdindex/rolap.db' as cdindex;
CREATE INDEX IF NOT EXISTS cdindex.cdindex_doi_idx ON cdindex(doi);

CREATE TABLE rolap.baseline_cdindex AS
  SELECT works.published_year, works.issn_print, Avg(cdindex) AS cdindex
    FROM works
    INNER JOIN cdindex ON works.doi = cdindex.doi
    GROUP BY published_year, issn_print;
