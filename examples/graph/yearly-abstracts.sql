-- Works with abstract and subject by year

SELECT published_year, Count(*) AS total,
    Coalesce(Count(abstract), 0) AS abstract
  FROM works
  WHERE published_year is not null
  GROUP BY published_year
  ORDER BY published_year;
