-- Calculate work citations

CREATE INDEX IF NOT EXISTS rolap.works_issn_doi_idx ON works_issn(doi);

CREATE INDEX IF NOT EXISTS rolap.works_issn_id_idx ON works_issn(id);

CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id);

CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);

CREATE TABLE rolap.citations AS
  SELECT cited_work.issn, COUNT(*) AS citations_number
  FROM work_references
  INNER JOIN rolap.works_issn AS citing_work
    ON work_references.work_id = citing_work.id
  INNER JOIN rolap.works_issn AS cited_work
    ON work_references.doi = cited_work.doi
  WHERE citing_work.published_year = 2021
    AND cited_work.published_year BETWEEN 2019 AND 2020
  GROUP BY cited_work.issn;
