-- Calculate the Two-Year Citation Mean
-- Note: This metric resembles the Journal Impact Factor.

CREATE TABLE rolap.citation_mean_2y AS
  SELECT publications2.journal_id,
    Coalesce(citations_number, 0) AS citations_number, publications_number,
    Cast(Coalesce(citations_number, 0) AS FLOAT) / publications_number
      AS citation_mean
  FROM rolap.publications2
  LEFT JOIN rolap.citations2
    ON rolap.citations2.journal_id = rolap.publications2.journal_id
  WHERE publications_number > 0;