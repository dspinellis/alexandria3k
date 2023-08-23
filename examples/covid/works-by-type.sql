-- Report the type of works in the data set
SELECT type, Count(*) FROM works GROUP BY type ORDER BY Count(*) DESC;
