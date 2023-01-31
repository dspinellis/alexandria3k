ATTACH DATABASE '../cdindex/rolap.db' as cdindex;

CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);
CREATE INDEX IF NOT EXISTS cdindex.cdindex_doi_idx ON cdindex(doi);

CREATE TABLE rolap.cdindex AS
  SELECT works.id AS work_id, cdindex FROM works
    INNER JOIN cdindex.cdindex ON works.doi = cdindex.doi;

CREATE INDEX IF NOT EXISTS rolap.cdindex_work_id_idx ON cdindex(work_id);
CREATE INDEX IF NOT EXISTS rolap.cdindex_cdindex_idx ON cdindex(cdindex);
