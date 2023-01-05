-- Calculate h5-index for each ORCID
CREATE INDEX IF NOT EXISTS rolap.works_orcid_doi_idx ON works_orcid(doi);
CREATE INDEX IF NOT EXISTS rolap.works_orcid_orcid_idx ON works_orcid(orcid);
CREATE INDEX IF NOT EXISTS rolap.work_citations_doi_idx ON work_citations(doi);

CREATE TABLE rolap.orcid_h5 AS
  WITH ranked_orcid_citations AS (
    SELECT orcid, citations_number,
      Row_number() OVER (
        PARTITION BY orcid ORDER BY citations_number DESC) AS row_rank
    FROM rolap.work_citations
    INNER JOIN rolap.works_orcid ON rolap.works_orcid.doi
      = rolap.work_citations.doi
  ),
  eligible_ranks AS (
    SELECT orcid, row_rank FROM ranked_orcid_citations
    WHERE row_rank <= citations_number
  )
  SELECT orcid, Max(row_rank) AS h5_index FROM eligible_ranks
  GROUP BY orcid;
