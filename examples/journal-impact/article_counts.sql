-- Calculate article counts for the Journal Network Centrality calculation (5-year window)
--
-- This script creates the `rolap.article_counts` table, which stores the number of
-- citable works for each journal within the 5-year window preceding the reference year.
-- This count serves as the "Article Vector" in the network centrality algorithm, used to
-- distribute the influence of dangling nodes (journals that don't cite others).
--
-- Note: This metric resembles the Eigenfactor score.
--
-- Dependencies:
--   - rolap.reference: Contains the reference year.
--   - rolap.citable_works: Contains the list of citable works with their publication year.

-- Ensure indexes exist for efficient querying
CREATE INDEX IF NOT EXISTS rolap.citable_works_published_year_idx ON citable_works(published_year);
CREATE INDEX IF NOT EXISTS rolap.citable_works_journal_id_idx ON citable_works(journal_id);

CREATE TABLE rolap.article_counts AS
  SELECT journal_id, COUNT(*) AS article_count
  FROM rolap.citable_works
  WHERE published_year BETWEEN
    ((SELECT year FROM rolap.reference) - 5)
    AND ((SELECT year FROM rolap.reference) - 1)
  GROUP BY journal_id;