-- Journals that are active (have publications) in the reference year.

CREATE INDEX IF NOT EXISTS rolap.works_journal_id_journal_id_idx
  ON works_journal_id(journal_id);

CREATE TABLE rolap.active_journals (id INTEGER PRIMARY KEY);

INSERT INTO rolap.active_journals (id)
  SELECT DISTINCT journal_id AS id
    FROM rolap.works_journal_id
    WHERE published_year = (SELECT year FROM rolap.reference);
