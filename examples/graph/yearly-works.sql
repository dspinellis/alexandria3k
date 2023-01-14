-- Number of works per year
SELECT * FROM rolap.yearly_works_all
WHERE published_year between 1950 and 2021
ORDER BY published_year;
