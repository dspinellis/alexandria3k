-- Calculate h5-index for each journal

CREATE INDEX IF NOT EXISTS rolap.works_journal_id_doi_idx ON works_journal_id(doi);
CREATE INDEX IF NOT EXISTS rolap.works_journal_id_journal_id_idx ON works_journal_id(journal_id);
CREATE INDEX IF NOT EXISTS rolap.work_citations_doi_idx ON work_citations(doi);

CREATE TABLE rolap.journal_h5 AS
  WITH ranked_journal_citations AS (
    SELECT journal_id, citations_number,
      Row_number() OVER (
        PARTITION BY journal_id ORDER BY citations_number DESC) AS row_rank
    FROM rolap.work_citations
    INNER JOIN rolap.works_journal_id ON rolap.works_journal_id.doi
      = rolap.work_citations.doi
  ),

  eligible_ranks AS (
    SELECT journal_id, row_rank FROM ranked_journal_citations
    WHERE row_rank <= citations_number
  ),

  h_index AS (
    SELECT journal_id, Max(row_rank) AS h5_index FROM eligible_ranks
    GROUP BY journal_id
  ),

  -- Select h-core rows for each journal.
  h_core AS (
    SELECT r.journal_id, r.citations_number
    FROM ranked_journal_citations AS r
    JOIN h_index h
      ON r.journal_id = h.journal_id AND r.row_rank <= h.h5_index
  ),

  -- Rank h-core by citations ASC for median.
  h_core_ranked AS (
      SELECT
          journal_id,
          citations_number,
          ROW_NUMBER() OVER (
              PARTITION BY journal_id
              ORDER BY citations_number
          ) AS rn,
          COUNT(*) OVER (
              PARTITION BY journal_id
          ) AS n
      FROM h_core
  ),

  -- median: middle element(s) depending on n being odd/even
  median AS (
      SELECT
          journal_id,
          AVG(citations_number) AS h5_median
      FROM h_core_ranked
      WHERE rn IN ( (n + 1) / 2, (n + 2) / 2 )
      GROUP BY journal_id
  )

  SELECT
      h_index.journal_id,
      h_index.h5_index,
      median.h5_median
  FROM h_index
  JOIN median USING (journal_id);
