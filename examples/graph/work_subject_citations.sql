-- Number of citations for each field pair
CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);

CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id);

CREATE INDEX IF NOT EXISTS works_asjcs_work_id_idx ON works_asjcs(work_id);

CREATE INDEX IF NOT EXISTS works_asjcs_asjc_id_idx ON works_asjcs(asjc_id);

CREATE TABLE rolap.work_subject_citations AS
  SELECT
      citing_subjects.asjc_id AS citing_subject_id,
      cited_subjects.asjc_id AS cited_subject_id,
      Count(*) AS citations_number
    FROM works AS citing_works
    INNER JOIN work_references ON citing_works.id = work_references.work_id
    INNER JOIN works AS cited_works ON cited_works.doi = work_references.doi
    INNER JOIN works_asjcs AS citing_subjects
      ON citing_subjects.work_id = citing_works.id
    INNER JOIN works_asjcs AS cited_subjects
      ON cited_subjects.work_id = cited_works.id
    GROUP BY citing_subject_id, cited_subject_id;
