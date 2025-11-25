-- Top ten publishers
-- Publisher|Publications
SELECT  Upper(publisher), Count(*) FROM works
GROUP BY Upper(publisher)
ORDER BY Count(*) DESC
LIMIT 10;
