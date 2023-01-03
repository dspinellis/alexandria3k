-- COVID-related topics researched

CREATE INDEX IF NOT EXISTS works_asjcs_asjc_id_idx ON works_asjcs(asjc_id);

CREATE INDEX IF NOT EXISTS asjcs_id_idx ON asjcs(id);

SELECT Rank() OVER (ORDER BY Count(*) DESC) AS rank, Count(*) AS number, field
  FROM works_asjcs
  INNER JOIN asjcs ON works_asjcs.asjc_id = asjcs.id
  GROUP BY asjc_id;
