-- Output the 100 most-common family names and their count

SELECT family_name, Count(*) AS n
  FROM persons
  GROUP BY family_name
  ORDER BY n DESC
  LIMIT 100;
