-- Citations per publication
CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);

CREATE TABLE rolap.work_citations AS
  SELECT doi, COUNT(*) AS citations_number
  FROM work_references
  GROUP BY doi;
