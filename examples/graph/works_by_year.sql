SELECT published_year, Count(*) AS number
FROM works
WHERE published_year between 1950 and 2021
GROUP BY published_year
ORDER BY published_year;
