SELECT yearly_works.year, Cast(yearly_works.n AS float) / yearly_authors.n AS n
  FROM rolap.yearly_works
  INNER JOIN rolap.yearly_authors
    ON yearly_works.year = yearly_authors.year;
