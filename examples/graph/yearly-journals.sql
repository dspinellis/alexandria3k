-- Yearly journals publishing works
WITH
  issns AS (
    SELECT published_year, Coalesce(issn_print, issn_electronic) AS issn
    FROM works
    WHERE published_year BETWEEN 1950 and 2021
      AND issn is not null
  )
SELECT published_year, Count(issn)
FROM issns
GROUP BY published_year
ORDER BY published_year;
