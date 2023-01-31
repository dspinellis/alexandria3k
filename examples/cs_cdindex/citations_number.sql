CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);
CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE TABLE rolap.citations_number AS
  SELECT cited_work.id AS work_id, COUNT(*) AS n
  FROM work_references
  INNER JOIN works AS cited_work
    ON work_references.doi = cited_work.doi
  GROUP BY cited_work.id;
