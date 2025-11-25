-- Top ten publication venues
-- Venue|Publications
SELECT  container_title, Count(*) FROM works
  WHERE container_title IS NOT null
  GROUP BY container_title
  ORDER BY Count(*) DESC
  LIMIT 10;
