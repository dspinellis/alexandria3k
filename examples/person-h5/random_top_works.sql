CREATE INDEX IF NOT EXISTS work_authors_orcid_idx ON work_authors(orcid);

CREATE TABLE rolap.random_top_works AS
  WITH top_orcids AS (
    SELECT orcid, h5_index FROM rolap.orcid_h5 WHERE h5_index > 50
  ),
  top_author_works AS (
    SELECT DISTINCT works.doi, h5_index FROM top_orcids
    INNER JOIN work_authors ON work_authors.orcid = top_orcids.orcid
    INNER JOIN works ON work_authors.work_id = works.id
  ),
  top_work_citations AS (
    SELECT works.id, citations_number FROM top_author_works
    INNER JOIN works ON top_author_works.doi = works.doi
    INNER JOIN rolap.work_citations ON work_citations.doi = top_author_works.doi
    WHERE work_citations.citations_number >= h5_index
  )
  SELECT DISTINCT id, citations_number FROM top_work_citations
  -- Deterministic pseudo-random order (can't seed SQLite Random())
  -- https://stackoverflow.com/a/24511461/20520
  ORDER BY substr(id * 0.54534238371923827955579364758491, length(id) + 2)
  LIMIT 50;
