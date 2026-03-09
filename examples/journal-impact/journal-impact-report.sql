-- The final report of journal impact metrics

.mode csv
.headers on

SELECT * FROM rolap.journal_impact ORDER BY title;
