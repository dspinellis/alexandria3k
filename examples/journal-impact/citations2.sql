-- Calculate work citations

CREATE INDEX IF NOT EXISTS rolap.works_journal_id_doi_idx ON works_journal_id(doi);

CREATE INDEX IF NOT EXISTS rolap.works_journal_id_id_idx ON works_journal_id(id);

CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id);

CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);

CREATE TABLE rolap.citations2 AS
  SELECT cited_work.journal_id, COUNT(*) AS citations_number
  FROM work_references
  INNER JOIN rolap.works_journal_id AS citing_work
    ON work_references.work_id = citing_work.id
  INNER JOIN rolap.works_journal_id AS cited_work
    ON work_references.doi = cited_work.doi
  WHERE cited_work.journal_id IS NOT null
    AND citing_work.published_year = (SELECT year FROM rolap.reference)
    AND cited_work.published_year BETWEEN
      ((SELECT year FROM rolap.reference) - 2)
      AND ((SELECT year FROM rolap.reference) - 1)
  GROUP BY cited_work.journal_id;
