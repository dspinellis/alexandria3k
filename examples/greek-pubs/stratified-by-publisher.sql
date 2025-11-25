-- Stratified random sample of five publications by publisher
-- Publisher|DOI|Title
WITH top10 AS (
    SELECT UPPER(publisher) AS pub
    FROM works
    GROUP BY UPPER(publisher)
    ORDER BY COUNT(*) DESC
    LIMIT 10
),
strat AS (
    SELECT
        title,
        doi,
        UPPER(publisher) AS pub,
        ROW_NUMBER() OVER (
            PARTITION BY UPPER(publisher)
            ORDER BY RANDOM()
        ) AS rn
    FROM works
    WHERE UPPER(publisher) IN (SELECT pub FROM top10)
)
SELECT pub, doi, title
FROM strat
WHERE rn <= 5;
