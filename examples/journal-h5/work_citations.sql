-- Count number of citations to each work
CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);

CREATE TABLE rolap.work_citations AS
  SELECT doi, COUNT(*) AS citations_number
  FROM work_references
  WHERE doi is not null
  GROUP BY doi;
