-- Yearly journals publishing works
WITH
  issns AS (
    SELECT published_year, Coalesce(issn_print, issn_electronic) AS issn
    FROM works
    WHERE published_year BETWEEN 1945 and 2021
      AND issn is not null
  ),
  issns_by_year AS (
    SELECT published_year, issn
    FROM issns
    GROUP BY published_year, issn
  )
SELECT published_year, Count(*) AS n
FROM issns_by_year
GROUP BY published_year
ORDER BY published_year;
