-- Average number of pages in an article per year
SELECT year, Avg(num_pages) AS n
FROM rolap.works_pages
-- Exclude 164387 records of a form like 1744-8069-5-32|6326
WHERE num_pages < 1000
GROUP BY year
ORDER BY year;
