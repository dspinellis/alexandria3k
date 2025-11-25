-- Top ten publication venues
-- Venue|Publications
SELECT  container_title, Count(*) FROM works
GROUP BY container_title
ORDER BY Count(*) DESC
LIMIT 10;
