-- Calculate h5-index for each ISSN

CREATE INDEX IF NOT EXISTS rolap.works_issn_doi_idx ON works_issn(doi);
CREATE INDEX IF NOT EXISTS rolap.works_issn_issn_idx ON works_issn(issn);
CREATE INDEX IF NOT EXISTS rolap.work_citations_doi_idx ON work_citations(doi);

CREATE TABLE rolap.issn_h5 AS
  WITH ranked_issn_citations AS (
    SELECT issn, citations_number,
      Row_number() OVER (
        PARTITION BY issn ORDER BY citations_number DESC) AS row_rank
    FROM rolap.work_citations
    INNER JOIN rolap.works_issn ON rolap.works_issn.doi
      = rolap.work_citations.doi
  ),
  eligible_ranks AS (
    SELECT issn, row_rank FROM ranked_issn_citations
    WHERE row_rank <= citations_number
  )
  SELECT issn, Max(row_rank) AS h5_index FROM eligible_ranks
  GROUP BY issn;
