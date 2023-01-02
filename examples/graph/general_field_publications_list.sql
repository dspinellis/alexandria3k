WITH top_names AS (
  SELECT name
  FROM general_field_publications
  GROUP BY name
  ORDER BY Sum(number) DESC
  limit 10
),

top_and_others AS (
  SELECT
    CASE
      WHEN name IN (SELECT name FROM top_names) THEN name
      ELSE "Others"
    END name,
    number, published_year
  FROM general_field_publications
  WHERE published_year between 1950 and 2021
)

SELECT published_year, name, Sum(number)
FROM top_and_others
GROUP BY published_year, name
ORDER BY published_year, name
