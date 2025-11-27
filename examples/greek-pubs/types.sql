-- Types of publications
-- Type|Number of works
SELECT  type, Count(*)
  FROM works
  GROUP BY type
  ORDER BY Count(*) DESC;
