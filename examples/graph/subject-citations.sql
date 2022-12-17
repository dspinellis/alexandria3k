DROP TABLE IF EXISTS work_subject_citations;

.print CREATE TABLE work_subject_citations
CREATE TABLE work_subject_citations AS
  SELECT
      citing_subjects.subject_id AS citing_subject_id,
      cited_subjects.subject_id AS cited_subject_id,
      Count(*) AS citations_number
    FROM works AS citing_works
    INNER JOIN work_references ON citing_works.id = work_references.work_id
    INNER JOIN works AS cited_works ON cited_works.doi = work_references.doi
    INNER JOIN works_subjects AS citing_subjects
      ON citing_subjects.work_id = citing_works.id
    INNER JOIN works_subjects AS cited_subjects
      ON cited_subjects.work_id = cited_works.id
    GROUP BY citing_subject_id, cited_subject_id;

CREATE INDEX work_subject_citations_citing_subject_id_idx
  ON work_subject_citations(citing_subject_id);

CREATE INDEX work_subject_citations_cited_subject_id_idx
  ON work_subject_citations(cited_subject_id);

DROP TABLE IF EXISTS subject_pair_dominance;

-- This is what Robert Martin calls instability (Chapter 20, Agile Software
-- Development). In our case it expresses dominance in a pair relationship:
-- 0.5 is equality, 1 is full dominance, 0 is full subjugation
.print CREATE TABLE subject_pair_dominance
CREATE TABLE subject_pair_dominance AS
  SELECT
      citing.citing_subject_id, citing.cited_subject_id,
      Cast(citing.citations_number AS float)
        / (citing.citations_number + cited.citations_number)
          AS citing_dominance
      FROM work_subject_citations AS citing
      INNER JOIN work_subject_citations AS cited
        ON citing.citing_subject_id = cited.cited_subject_id AND
           citing.cited_subject_id = cited.citing_subject_id;

DROP TABLE IF EXISTS subject_pair_strength;

-- Relative strength of subject relationships (0-1)
.print CREATE TABLE subject_pair_strength
CREATE TABLE  subject_pair_strength AS
  WITH subject_pair_absolute_strength AS (
    SELECT
        citing.citing_subject_id, citing.cited_subject_id,
          citing.citations_number + cited.citations_number AS strength
        FROM work_subject_citations AS citing
        INNER JOIN work_subject_citations AS cited
          ON citing.citing_subject_id = cited.cited_subject_id AND
             citing.cited_subject_id = cited.citing_subject_id
        WHERE citing.citing_subject_id != citing.cited_subject_id
  ),
  max_strength AS (
    SELECT Max(strength) value
      FROM subject_pair_absolute_strength
  )
  SELECT citing_subject_id, cited_subject_id,
      Cast(strength AS float) / (SELECT value FROM max_strength) AS strength
    FROM subject_pair_absolute_strength;

-- List pair relationships with a high dominance and strenth
SELECT citing_subject_names.name AS citing_subject_name,
    cited_subject_names.name AS cited_subject_name,
    subject_pair_dominance.citing_dominance, subject_pair_strength.strength
  FROM subject_pair_dominance
  INNER JOIN subject_pair_strength
    ON subject_pair_dominance.citing_subject_id
      = subject_pair_strength.cited_subject_id AND
     subject_pair_dominance.cited_subject_id
      = subject_pair_strength.citing_subject_id
  LEFT JOIN subject_names AS citing_subject_names
    ON citing_subject_names.subject_id
      = subject_pair_dominance.citing_subject_id
  LEFT JOIN subject_names AS cited_subject_names
    ON cited_subject_names.subject_id
      = subject_pair_dominance.cited_subject_id
  WHERE subject_pair_dominance.citing_subject_id
    != subject_pair_dominance.cited_subject_id AND
    subject_pair_dominance.citing_dominance + subject_pair_strength.strength > 1.8;
