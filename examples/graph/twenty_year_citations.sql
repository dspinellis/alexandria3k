-- Citations published each year for publications in the two preceding years

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);

CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);

CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id);

CREATE TABLE rolap.twenty_year_citations AS
  SELECT citing_work.published_year AS year, COUNT(*) AS citations_number
  FROM work_references
  INNER JOIN works AS citing_work
    ON work_references.work_id = citing_work.id
  INNER JOIN works AS cited_work
    ON work_references.doi = cited_work.doi
  WHERE citing_work.published_year BETWEEN 1945 and 2021
    AND cited_work.published_year BETWEEN citing_work.published_year - 20
      AND citing_work.published_year - 1
  GROUP BY year;
