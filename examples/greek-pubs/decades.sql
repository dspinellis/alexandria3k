-- Publications by published decade
-- Decade|Number of works
-- Note: Most publications appear to lack a publication year. EKT PhDs appear to be “approved” rather than published, therefore they lack a publication year.
SELECT  (published_year / 10) * 10 AS decade, Count(*) FROM works
WHERE published_year IS NOT null
GROUP BY decade
ORDER BY decade;
