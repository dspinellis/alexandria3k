-- Calculate the journal impact factor

CREATE TABLE rolap.impact_factor5 AS
  SELECT publications5.journal_id,
    Coalesce(citations_number, 0) AS citations_number, publications_number,
    Cast(Coalesce(citations_number, 0) AS FLOAT) / publications_number
      AS impact_factor
  FROM rolap.publications5
  LEFT JOIN rolap.citations5
    ON rolap.citations5.journal_id = rolap.publications5.journal_id
  WHERE publications_number > 0;
