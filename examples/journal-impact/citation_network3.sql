-- Create table for citation network for prestige rank calculation (3-year window)
--
-- This script creates the `rolap.citation_network3` table, which aggregates citations
-- between journals using a 3-year citation window.
-- It counts how many times a "citing journal" cited a "cited journal"
-- within the specific time window (citations from the reference year to works published
-- in the preceding 3 years).
--
-- Unlike the network centrality citation_network, this table INCLUDES self-citations,
-- as prestige rank limits (rather than excludes) self-citations to 33% of incoming citations.
--
-- Dependencies:
--   - rolap.reference: Contains the reference year.
--   - rolap.works_journal_id: Maps works to journals and publication years.
--   - work_references: Contains the raw citation links between works.

-- Ensure indexes exist for efficient querying
CREATE INDEX IF NOT EXISTS rolap.works_journal_id_doi_idx ON works_journal_id(doi);
CREATE INDEX IF NOT EXISTS rolap.works_journal_id_id_idx ON works_journal_id(id);
CREATE INDEX IF NOT EXISTS rolap.works_journal_id_journal_id_idx ON works_journal_id(journal_id);
CREATE INDEX IF NOT EXISTS rolap.works_journal_id_published_year_idx ON works_journal_id(published_year);

CREATE INDEX IF NOT EXISTS work_references_work_id_idx ON work_references(work_id);
CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);

CREATE TABLE rolap.citation_network3 AS
  SELECT
    citing_work.journal_id AS citing_journal,
    cited_work.journal_id AS cited_journal,
    COUNT(*) AS citation_count
  FROM work_references
  INNER JOIN rolap.works_journal_id AS citing_work
    ON work_references.work_id = citing_work.id
  INNER JOIN rolap.works_journal_id AS cited_work
    ON work_references.doi = cited_work.doi
  WHERE cited_work.journal_id IS NOT null
    AND citing_work.journal_id IS NOT null
    AND citing_work.published_year = (SELECT year FROM rolap.reference)
    AND cited_work.published_year BETWEEN
      ((SELECT year FROM rolap.reference) - 3)
      AND ((SELECT year FROM rolap.reference) - 1)
  GROUP BY citing_work.journal_id, cited_work.journal_id;
