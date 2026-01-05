-- Average reference count per journal (citation density)
--
-- Dependencies:
--   - rolap.works_journal_id: Work-to-journal mapping
--   - rolap.work_reference_count: References per work
--   - rolap.reference: Reference year

CREATE INDEX IF NOT EXISTS rolap.works_journal_id_id_idx
  ON works_journal_id(id);
CREATE INDEX IF NOT EXISTS rolap.works_journal_id_journal_id_idx
  ON works_journal_id(journal_id);
CREATE INDEX IF NOT EXISTS rolap.works_journal_id_published_year_idx
  ON works_journal_id(published_year);
CREATE INDEX IF NOT EXISTS rolap.work_reference_count_idx
  ON work_reference_count(work_id);

CREATE TABLE rolap.journal_reference_density AS
  SELECT
    wj.journal_id,
    AVG(wrc.reference_count) AS avg_references,
    COUNT(DISTINCT wj.id) AS work_count
  FROM rolap.works_journal_id wj
  INNER JOIN rolap.work_reference_count wrc
    ON wj.id = wrc.work_id
  WHERE wj.published_year = (SELECT year FROM rolap.reference)
  GROUP BY wj.journal_id;
