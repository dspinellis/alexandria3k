-- Obtain work-record metrics not available from the graph
WITH counts AS (
  -- Get all measures in a single pass
  SELECT type, abstract is not null AS have_abstract,
    Count(*) AS number
  FROM   works
  GROUP by type, have_abstract
)
-- Disaggregate them
SELECT 'type' as metric, type AS name, Sum(number)
  FROM counts GROUP BY type
UNION
SELECT 'abstract' as metric, have_abstract AS name, Sum(number)
  FROM counts GROUP BY have_abstract;
