-- Reference count per work (for citation potential calculation)
--
-- Dependencies:
--   - work_references: Individual references from works

CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id);

CREATE TABLE rolap.work_reference_count AS
  SELECT
    work_id,
    COUNT(*) AS reference_count
  FROM work_references
  GROUP BY work_id;
