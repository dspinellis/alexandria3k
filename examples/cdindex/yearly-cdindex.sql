-- Calculate average CD-5 index per year
SELECT Cast(Strftime('%Y', datetime(timestamp, 'unixepoch')) AS int) AS year,
    Avg(cdindex) AS cdindex
  FROM rolap.cdindex
  WHERE cdindex is not null
  GROUP BY year
  -- Years to 2021 are needed for calculating CD5
  HAVING year <= 2016;
