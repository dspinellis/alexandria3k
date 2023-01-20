-- Calculate average CD-5 index per year
SELECT Strftime('%Y', timestamp) AS year, Avg(cdindex) AS cdindex
  FROM rolap.cdindex
  WHERE cdindex is not null
  GROUP BY year;
