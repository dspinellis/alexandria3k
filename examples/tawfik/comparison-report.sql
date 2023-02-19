-- Compare average CD5 values

.print Dan Tawfik average CD5
SELECT Avg(t_cd5) FROM comparison WHERE t_cd5 is not null;

.print Baseline average CD5
SELECT Avg(b_cd5) FROM comparison WHERE b_cd5 is not null;

.print Dan Tawfik average CD5 top-20
SELECT avg(t_cd5) FROM (
  SELECT t_cd5 FROM comparison ORDER BY t_cd5 DESC limit 20
);

.print Baseline average CD5 top-20
SELECT avg(b_cd5) FROM (
  SELECT b_cd5 FROM comparison ORDER BY b_cd5 DESC limit 20
);
