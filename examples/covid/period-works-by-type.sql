-- Report the type of works in the same period as that of the COVID data set

SELECT type, Count(*) FROM works
  WHERE published_year >= 2020
  GROUP BY type ORDER BY Count(*) DESC;
