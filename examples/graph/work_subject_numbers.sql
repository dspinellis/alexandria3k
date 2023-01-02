-- Number of works for each field subject
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS works_asjcs_work_id_idx ON works_asjcs(work_id);

CREATE INDEX IF NOT EXISTS works_asjcs_asjc_id_idx ON works_asjcs(asjc_id);

CREATE TABLE rolap.work_subject_numbers AS
  SELECT works_asjcs.asjc_id, Count(*) AS number
    FROM works
    INNER JOIN works_asjcs ON works_asjcs.work_id = works.id
    GROUP BY works_asjcs.asjc_id;
