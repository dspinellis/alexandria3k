-- COVID research citing other COVID research
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id);

CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);

CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);

SELECT original_works.published_year, original_works.published_month,
    Count(*) AS number
  FROM works AS original_works
  INNER JOIN work_references ON work_references.work_id = original_works.id
  INNER JOIN works AS cited_works ON work_references.doi = cited_works.doi
  GROUP BY original_works.published_year, original_works.published_month
  ORDER BY original_works.published_year, original_works.published_month;
