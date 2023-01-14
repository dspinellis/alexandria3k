-- Authors with at least 10 consecutive year publication streaks
WITH 
  streaks AS (
    SELECT 
      orcid,
      year,
      year - Row_number() OVER (PARTITION BY orcid ORDER BY year) AS streak_id
    FROM rolap.author_year_works
  )
SELECT orcid, Count(*) AS streak, Min(year) AS starting_year
FROM streaks
GROUP BY orcid, streak_id
HAVING streak >= 10
ORDER BY streak DESC;
