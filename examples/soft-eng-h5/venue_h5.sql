-- Calculate h5-index for each venue

CREATE INDEX IF NOT EXISTS rolap.works_venu_doi_idx ON works_venue(doi);

CREATE INDEX IF NOT EXISTS rolap.work_citations_doi_idx ON work_citations(doi);

CREATE TABLE rolap.venue_h5 AS
  WITH ranked_venue_citations AS (
    SELECT venue, citations_number,
      Row_number() OVER (
        PARTITION BY venue ORDER BY citations_number DESC) AS row_rank
    FROM rolap.work_citations
    INNER JOIN rolap.works_venue ON works_venue.doi = work_citations.doi
  ),
  eligible_ranks AS (
    SELECT venue, row_rank FROM ranked_venue_citations
    WHERE row_rank <= citations_number
  )
  SELECT venue, Max(row_rank) AS h5_index FROM eligible_ranks
  GROUP BY venue;

