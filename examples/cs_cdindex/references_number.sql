CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id);

CREATE TABLE rolap.references_number AS
  SELECT work_id, COUNT(*) AS n
  FROM work_references
  GROUP BY work_id;
