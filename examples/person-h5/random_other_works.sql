CREATE INDEX IF NOT EXISTS rolap.work_citations_citations_number_idx
  ON work_citations(citations_number);

CREATE INDEX IF NOT EXISTS rolap.random_top_works_citations_number_idx
  ON random_top_works(citations_number);

CREATE TABLE rolap.random_other_works AS
  WITH candidate_works AS (
    SELECT random_top_works.id AS top_work_id,
      works.id AS other_work_id,
      random_top_works.citations_number
    FROM rolap.random_top_works
    LEFT JOIN rolap.work_citations
      ON random_top_works.citations_number = work_citations.citations_number
    INNER JOIN works ON work_citations.doi = works.doi
    WHERE works.id  != random_top_works.id
  ),
  random_candidate_works AS (
    SELECT other_work_id, citations_number,
    Row_number() OVER (
      PARTITION BY top_work_id
      -- Deterministic pseudo-random order (can't seed SQLite Random())
      -- https://stackoverflow.com/a/24511461/20520
      ORDER BY substr(other_work_id * 0.54534238371923827955579364758491,
        length(other_work_id) + 2)

    ) AS n
    FROM candidate_works
  )
  SELECT other_work_id AS id, citations_number from random_candidate_works
  WHERE n = 1;
