-- Authors who have published more than 72 papers in any one year
SELECT orcid, year, articles FROM rolap.author_year_works
WHERE articles > 72
ORDER BY articles DESC, year;
