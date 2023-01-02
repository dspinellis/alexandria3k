-- This is what Robert Martin calls instability (Chapter 20, Agile Software
-- Development). In our case it expresses dominance in a pair relationship:
-- 0.5 is equality, 1 is full dominance, 0 is full subjugation
CREATE TABLE rolap.subject_pair_fundamentalness_percentile AS
  WITH subject_pair_fundamentalness AS (
    SELECT
        cited.citing_subject_id, cited.cited_subject_id,
        citing.citations_number AS citing_citations_number,
        cited.citations_number AS cited_citations_number,
        Cast(citing.citations_number AS float)
          / (Coalesce(citing.citations_number, 0) + cited.citations_number)
            AS cited_fundamentalness
        FROM rolap.work_subject_citations AS cited
        LEFT JOIN rolap.work_subject_citations AS citing
          ON citing.citing_subject_id = cited.cited_subject_id AND
             citing.cited_subject_id = cited.citing_subject_id
    )
  SELECT *, NTILE(100) OVER(ORDER BY cited_fundamentalness ASC) AS percentile
  FROM subject_pair_fundamentalness;
