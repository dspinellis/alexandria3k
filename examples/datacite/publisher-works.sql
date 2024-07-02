-- List of publishers and works ordered  y number of works for each

SELECT publisher, Count(*) AS n
  FROM dc_works GROUP BY publisher ORDER BY n DESC;
