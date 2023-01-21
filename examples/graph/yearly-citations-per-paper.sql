-- Average number of citations each paper receives per year
-- Example: 1960 All published works until then: 1M
-- References made on that year: 3M
-- Ratio: 3/1

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS work_references_work_id_idx
  ON work_references(work_id);

WITH
  total_works_by_year AS (
    SELECT published_year, Sum(n) OVER (ORDER BY published_year) AS n
    FROM rolap.yearly_works_all
  ),
  references_by_year AS (
    SELECT published_year, Count(*) AS n
    FROM works
    INNER JOIN work_references ON works.id = work_references.work_id
    WHERE published_year BETWEEN 1945 and 2021
    GROUP BY published_year
  )
SELECT references_by_year.published_year, 
  Cast(references_by_year.n AS float) / total_works_by_year.n
FROM total_works_by_year
INNER JOIN references_by_year
  ON total_works_by_year.published_year = references_by_year.published_year
ORDER BY references_by_year.published_year;
