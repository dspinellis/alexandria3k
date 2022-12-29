.print CREATE INDEX works_doi_idx
CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);

.print CREATE INDEX works_id_idx
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

.print CREATE INDEX work_references_doi_idx
CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);

.print CREATE INDEX work_references_work_id_idx
CREATE INDEX IF NOT EXISTS work_references_work_id_idx ON work_references(work_id);

.print CREATE INDEX works_asjcs_work_id_idx
CREATE INDEX IF NOT EXISTS works_asjcs_work_id_idx ON works_asjcs(work_id);

.print CREATE INDEX works_asjcs_asjc_id_idx
CREATE INDEX IF NOT EXISTS works_asjcs_asjc_id_idx ON works_asjcs(asjc_id);


.print CREATE TABLE work_subject_citations
CREATE TABLE work_subject_citations AS
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

