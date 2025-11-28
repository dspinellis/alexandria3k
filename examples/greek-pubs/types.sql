-- Types of publications
-- Type|Number of works
SELECT  type, Count(*)
  FROM rolap.cleaned_works
  GROUP BY type
  ORDER BY Count(*) DESC;
