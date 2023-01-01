-- Pair relationships with a high fundamentalness and strength
CREATE TABLE sh.subject_hierarchy AS
  SELECT
      citing_subject_names.field AS citing_subject_name,
      citing_subject_names.id AS citing_subject_id,
      subject_pair_fundamentalness_percentile.citing_citations_number,
      cited_subject_names.field AS cited_subject_name,
      cited_subject_names.id AS cited_subject_id,
      subject_pair_fundamentalness_percentile.cited_citations_number,
      subject_pair_fundamentalness_percentile.cited_fundamentalness,
      subject_pair_strength_percentile.strength
    FROM subject_pair_fundamentalness_percentile
    INNER JOIN subject_pair_strength_percentile
      ON subject_pair_fundamentalness_percentile.citing_subject_id
        = subject_pair_strength_percentile.citing_subject_id AND
       subject_pair_fundamentalness_percentile.cited_subject_id
        = subject_pair_strength_percentile.cited_subject_id
    LEFT JOIN asjcs AS citing_subject_names
      ON citing_subject_names.id
        = subject_pair_fundamentalness_percentile.citing_subject_id
    LEFT JOIN asjcs AS cited_subject_names
      ON cited_subject_names.id
        = subject_pair_fundamentalness_percentile.cited_subject_id
    WHERE subject_pair_fundamentalness_percentile.citing_subject_id
      != subject_pair_fundamentalness_percentile.cited_subject_id
      AND subject_pair_fundamentalness_percentile.percentile > 90
      AND citing_subject_names.field != 'Multidisciplinary'
    ORDER BY
      subject_pair_strength_percentile.percentile DESC
    LIMIT 50;
