-- Frequent author names at the two ends of the studied period
-- These indicate possible clashes

CREATE INDEX IF NOT EXISTS works_id_idx ON works(id);

CREATE INDEX IF NOT EXISTS works_published_year_idx ON works(published_year);

CREATE INDEX IF NOT EXISTS work_authors_work_id_idx ON work_authors(work_id);

WITH
  author_activity AS (
    SELECT published_year,
      CASE
        WHEN given is null or length(given) < 1 THEN family
        ELSE Substr(given, 1, 1) || '. ' || family
      END name
    FROM work_authors
    INNER JOIN works on work_authors.work_id = works.id
    WHERE published_year IN (1945, 2021)
  ),
  common_1945 AS (
    SELECT 1945 AS year, name, Count(*) AS n
    FROM author_activity
    WHERE published_year = 1945
    GROUP BY name
    ORDER BY n DESC
    LIMIT 10
  ),
  all_1945 AS (
    SELECT 1945 AS year, 'All' AS name, Count(*) AS n
    FROM author_activity
    WHERE published_year = 1945
  ),
  common_2021 AS (
    SELECT 2021 AS year, name, Count(*) AS n
    FROM author_activity
    WHERE published_year = 2021
    GROUP BY name
    ORDER BY n DESC
    LIMIT 10
  ),
  all_2021 AS (
    SELECT 2021 AS year, 'All' AS name, Count(*) AS n
    FROM author_activity
    WHERE published_year = 2021
  )

SELECT * FROM common_1945
UNION
SELECT * FROM all_1945
UNION
SELECT * FROM common_2021
UNION
SELECT * FROM all_2021

ORDER BY year, n DESC;
