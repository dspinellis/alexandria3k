-- Generate a list of evolution in general field publications per year
WITH numbers_1945 AS (
  SELECT * FROM rolap.general_field_publications WHERE published_year = 1945
),
numbers_2021 AS (
  SELECT * FROM rolap.general_field_publications WHERE published_year = 2021
),
total_1945 AS (
  SELECT Cast(Count(*) AS FLOAT) FROM works WHERE published_year = 1945
),
total_2021 AS (
  SELECT Cast(Count(*)AS FLOAT) FROM works WHERE published_year = 2021
),
difference AS (
  SELECT numbers_2021.name,
    numbers_2021.number AS n2021, numbers_1945.number AS n1945,
    numbers_2021.number / (SELECT * FROM total_2021) * 100 AS percentage_2021,
    (numbers_2021.number / (SELECT * FROM total_2021)
      - numbers_1945.number / (SELECT * FROM total_1945))
      / (numbers_1945.number / (SELECT * FROM total_1945))
    AS change
  FROM numbers_1945
  INNER JOIN numbers_2021 ON numbers_1945.name = numbers_2021.name
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
      ELSE 'Others'
    END name,
    number, published_year
  FROM rolap.general_field_publications
  WHERE published_year between 1945 and 2021
)

SELECT published_year, name, Sum(number)
FROM top_and_others
GROUP BY published_year, name
ORDER BY published_year, name
