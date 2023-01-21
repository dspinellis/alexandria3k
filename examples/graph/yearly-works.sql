-- Number of works per year
SELECT * FROM rolap.yearly_works_all
WHERE published_year between 1945 and 2021
ORDER BY published_year;
