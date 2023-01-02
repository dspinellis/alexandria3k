CREATE INDEX IF NOT EXISTS works_published_year_idx ON works(published_year);

CREATE INDEX IF NOT EXISTS works_asjcs_work_id_idx ON works_asjcs(work_id);

CREATE INDEX IF NOT EXISTS works_asjcs_asjc_id_idx ON works_asjcs(asjc_id);

CREATE INDEX IF NOT EXISTS asjc_general_fields_id_idx ON
  asjc_general_fields(id);

CREATE TABLE rolap.general_field_publications AS
  WITH general_field_id_publications AS (
    SELECT
        asjcs.general_field_id, works.published_year, Count(*) AS number
      FROM works
      INNER JOIN works_asjcs ON works_asjcs.work_id = works.id
      INNER JOIN asjcs ON works_asjcs.asjc_id = asjcs.id
      WHERE works.published_year is not null
      GROUP BY asjcs.general_field_id, works.published_year
  )
  SELECT asjc_general_fields.name, published_year, number
  FROM general_field_id_publications
  INNER JOIN asjc_general_fields
    ON asjc_general_fields.id = general_field_id_publications.general_field_id;
