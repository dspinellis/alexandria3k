ATTACH DATABASE '../cdindex/rolap.db' as cdindex;
CREATE INDEX IF NOT EXISTS cdindex.cdindex_doi_idx ON cdindex(doi);

ATTACH DATABASE 'tawfik-works.db' as tw;
CREATE INDEX IF NOT EXISTS tw.tawfik_works_doi_idx ON tawfik_works(doi);

CREATE TABLE rolap.tawfik_cdindex AS
  SELECT tawfik_works.doi, tawfik_works.published_year,
      tawfik_works.issn_print, cdindex
    FROM tawfik_works
    INNER JOIN cdindex ON tawfik_works.doi = cdindex.doi;
