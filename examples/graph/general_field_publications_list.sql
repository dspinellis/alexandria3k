WITH numbers_1950 AS (
  SELECT * FROM general_field_publications WHERE published_year = 1950
),
numbers_2021 AS (
  SELECT * FROM general_field_publications WHERE published_year = 2021
),
total_1950 AS (
  SELECT Cast(Count(*) AS FLOAT) FROM works WHERE published_year = 1950
),
total_2021 AS (
  SELECT Cast(Count(*)AS FLOAT) FROM works WHERE published_year = 2021
),
difference AS (
  SELECT numbers_2021.name,
    numbers_2021.number AS n2021, numbers_1950.number AS n1950,
    numbers_2021.number / (SELECT * FROM total_2021) * 100 AS percentage_2021,
    (numbers_2021.number / (SELECT * FROM total_2021)
      - numbers_1950.number / (SELECT * FROM total_1950))
      / (numbers_1950.number / (SELECT * FROM total_1950))
    AS change
  FROM numbers_1950
  INNER JOIN numbers_2021 ON numbers_1950.name = numbers_2021.name
),
top_changing_names AS (
  SELECT name FROM difference
  WHERE percentage_2021 > 2
  ORDER BY Abs(change) DESC
  limit 10
),
top_and_others AS (
  SELECT
    CASE
      WHEN name IN (SELECT name FROM top_changing_names) THEN name
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
