CREATE TABLE  sh.subject_pair_strength_percentile AS
  WITH subject_pair_strength AS (
    SELECT
        citing.citing_subject_id, citing.cited_subject_id,
          citing.citations_number + cited.citations_number AS strength
        FROM work_subject_citations AS citing
        INNER JOIN work_subject_citations AS cited
          ON citing.citing_subject_id = cited.cited_subject_id AND
             citing.cited_subject_id = cited.citing_subject_id
        WHERE citing.citing_subject_id != citing.cited_subject_id
  )
  SELECT *, NTILE(100) OVER(ORDER BY strength ASC) AS percentile
  FROM subject_pair_strength;
