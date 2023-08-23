-- Number of open access journal papers per year

CREATE INDEX IF NOT EXISTS works_id_idx on works(id);
CREATE INDEX IF NOT EXISTS rolap.oa_works_work_id_idx on oa_works(work_id);

WITH oa_journal_papers AS (
  SELECT published_year, Count(*) AS n
    FROM works
    INNER JOIN rolap.oa_works ON works.id = oa_works.work_id
    WHERE published_year between 1945 and 2021
    GROUP BY published_year
),
non_oa_journal_papers AS (
  SELECT published_year, Count(*) AS n
    FROM works
    LEFT JOIN rolap.oa_works ON works.id = oa_works.work_id
    WHERE published_year between 1945 and 2021
      AND oa_works.work_id is null
    GROUP BY published_year
)
SELECT non_oa_journal_papers.published_year,
  non_oa_journal_papers.n AS non_oa_n,
  oa_journal_papers.n AS oa_n,
  Cast(oa_journal_papers.n AS float)
    / (non_oa_journal_papers.n + oa_journal_papers.n) AS oa_ratio
  FROM non_oa_journal_papers LEFT JOIN oa_journal_papers ON
    non_oa_journal_papers.published_year = oa_journal_papers.published_year;
