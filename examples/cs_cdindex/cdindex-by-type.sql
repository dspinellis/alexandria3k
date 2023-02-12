CREATE INDEX IF NOT EXISTS works_type_idx ON works(type);
CREATE INDEX IF NOT EXISTS rolap.cdindex_work_id_idx ON cdindex(work_id);
CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id);

SELECT type, Count(*), Avg(cdindex)
  FROM works
  INNER JOIN rolap.cdindex ON works.id = cdindex.work_id
  WHERE cdindex is not null
    AND EXISTS (
      SELECT 1 FROM work_references WHERE work_references.work_id = works.id)
  GROUP BY type;
