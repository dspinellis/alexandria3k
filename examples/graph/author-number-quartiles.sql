-- Output the quartiles of author number distribution
CREATE INDEX IF NOT EXISTS work_authors_work_id_idx ON work_authors(work_id);

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

WITH number_of_authors AS (
  SELECT Count(*) AS number FROM works
    LEFT JOIN work_authors ON works.id = work_authors.work_id
    WHERE published_year >= 2020
    GROUP BY works.id
),
quartiles AS (
  SELECT number, Ntile(4) Over(ORDER BY number ASC) AS quartile
  FROM number_of_authors
)
SELECT 'Q1' as name, Max(number) FROM quartiles WHERE quartile = 1
UNION
SELECT 'Q2' as name, Max(number) FROM quartiles WHERE quartile = 2
UNION
SELECT 'Q3' as name, Max(number) FROM quartiles WHERE quartile = 3;
