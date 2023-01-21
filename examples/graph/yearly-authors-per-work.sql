-- Yearly average number of authors per work
WITH
  work_author_number AS (
    SELECT work_id, Count(*) AS n
    FROM work_authors
    GROUP BY work_id
  ),
  work_author_year AS (
    SELECT published_year, n from work_author_number
    LEFT JOIN works on work_author_number.work_id = works.id
    WHERE published_year BETWEEN 1945 and 2021
  )
SELECT published_year, Avg(n)
FROM work_author_year
GROUP BY published_year
ORDER BY published_year;
