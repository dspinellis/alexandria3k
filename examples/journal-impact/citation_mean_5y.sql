-- Calculate the Five-Year Citation Mean
-- Note: This metric is similar to the 5-Year Impact Factor

CREATE TABLE rolap.citation_mean_5y AS
  SELECT publications5.journal_id,
    Coalesce(citations_number, 0) AS citations_number, publications_number,
    Cast(Coalesce(citations_number, 0) AS FLOAT) / publications_number
      AS citation_mean
  FROM rolap.publications5
  LEFT JOIN rolap.citations5
    ON rolap.citations5.journal_id = rolap.publications5.journal_id
  WHERE publications_number > 0;