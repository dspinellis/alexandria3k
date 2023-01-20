-- Calculate average CD-5 index per year
SELECT Strftime('%Y', datetime(timestamp, 'unixepoch')) AS year,
    Avg(cdindex) AS cdindex
  FROM rolap.cdindex
  WHERE cdindex is not null AND year >= 1950
  GROUP BY year;
