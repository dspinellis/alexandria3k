-- Applicants Population by Country and year for the Top 5 Countries of 2022
WITH ranked_countries AS (
       SELECT
           SUBSTRING(date_published, 1, 4) AS year,
           usp_applicants.country AS country,
           COUNT(*) AS patent_count,
           ROW_NUMBER() OVER(PARTITION BY SUBSTRING(date_published, 1, 4) ORDER BY COUNT(*) DESC) AS country_rank
       FROM us_patents
       INNER JOIN usp_applicants
       ON us_patents.container_id = usp_applicants.patent_id
       GROUP BY
           year, usp_applicants.country
  ),
  top_5_2022 AS (
       SELECT country
       FROM ranked_countries
       WHERE
           year = '2022' AND country_rank <= 5
  )
SELECT
      rc.year,
      rc.country,
      rc.patent_count
  FROM ranked_countries rc
  JOIN top_5_2022 t5
  ON
      rc.country = t5.country
  ORDER BY
      rc.year, rc.country;
