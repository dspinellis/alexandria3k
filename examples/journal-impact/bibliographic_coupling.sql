-- Bibliographic coupling between journals
--
-- Two journals are bibliographically coupled if they cite the same references.
-- The coupling strength is the number of shared references.
-- This creates a weighted undirected graph for community detection.
--
-- We use a 3-year window (t-1, t-2, t-3) for the context-normalized impact calculation.
-- Only consider references that are cited by at least 2 journals to reduce noise.

-- Ensure indexes exist for efficient querying
CREATE INDEX IF NOT EXISTS work_references_work_id_idx ON work_references(work_id);
CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);
CREATE INDEX IF NOT EXISTS rolap.works_journal_id_id_idx ON works_journal_id(id);
CREATE INDEX IF NOT EXISTS rolap.works_journal_id_journal_id_idx ON works_journal_id(journal_id);
CREATE INDEX IF NOT EXISTS rolap.works_journal_id_published_year_idx ON works_journal_id(published_year);

CREATE TABLE rolap.bibliographic_coupling AS
  WITH
  -- Get all references made by journals in the 3-year window
  journal_references AS (
    SELECT DISTINCT
      wj.journal_id,
      wr.doi AS reference_doi
    FROM work_references wr
    INNER JOIN rolap.works_journal_id wj ON wr.work_id = wj.id
    WHERE wj.journal_id IS NOT NULL
      AND wr.doi IS NOT NULL
      AND wj.published_year BETWEEN
        ((SELECT year FROM rolap.reference) - 3)
        AND ((SELECT year FROM rolap.reference) - 1)
  ),
  -- Count how many journals cite each reference (filter to shared refs)
  shared_references AS (
    SELECT reference_doi
    FROM journal_references
    GROUP BY reference_doi
    HAVING COUNT(DISTINCT journal_id) >= 2
  )
  -- Count shared references between each pair of journals
  SELECT
    jr1.journal_id AS journal_a,
    jr2.journal_id AS journal_b,
    COUNT(*) AS coupling_strength
  FROM journal_references jr1
  INNER JOIN journal_references jr2
    ON jr1.reference_doi = jr2.reference_doi
    AND jr1.journal_id < jr2.journal_id  -- Avoid duplicates (a,b) and (b,a)
  INNER JOIN shared_references sr
    ON jr1.reference_doi = sr.reference_doi
  GROUP BY jr1.journal_id, jr2.journal_id
  HAVING COUNT(*) >= 5;  -- Minimum coupling strength threshold
