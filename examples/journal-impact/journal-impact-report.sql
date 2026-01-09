-- Create a CSV file with the calculated 2-year and 5-year impact factors.

CREATE INDEX IF NOT EXISTS rolap.impact_factor2_journal_id_idx
  ON impact_factor2(journal_id);
CREATE INDEX IF NOT EXISTS rolap.impact_factor5_journal_id_idx
  ON impact_factor5(journal_id);
CREATE INDEX IF NOT EXISTS rolap.journal_h5_journal_id_idx
  ON journal_h5(journal_id);
CREATE INDEX IF NOT EXISTS rolap.sjr_journal_id_idx
  ON sjr(journal_id);
CREATE INDEX IF NOT EXISTS rolap.ais_journal_id_idx
  ON ais(journal_id);
CREATE INDEX IF NOT EXISTS rolap.snip_journal_id_idx
  ON snip(journal_id);
CREATE INDEX IF NOT EXISTS rolap.journal_communities_journal_id_idx
  ON journal_communities(journal_id);

.mode csv
.headers on

SELECT
    rolap.journal_names.title,
    rolap.journal_names.publisher,
    rolap.journal_names.issn_print,
    rolap.journal_names.issn_eprint,
    rolap.journal_names.issns_additional,
    rolap.journal_names.doi,
    rolap.impact_factor2.citations_number AS citations_number2,
    rolap.impact_factor2.publications_number AS publications_number2,
    Round(rolap.impact_factor2.impact_factor, 2) AS impact_factor2,
    rolap.impact_factor5.citations_number AS citations_number5,
    rolap.impact_factor5.publications_number AS publications_number5,
    Round(rolap.impact_factor5.impact_factor, 2) AS impact_factor5,
    rolap.journal_h5.h5_index,
    rolap.journal_h5.h5_median,
    Round(rolap.eigenfactor.eigenfactor_score, 5) AS eigenfactor_score,
    Round(rolap.sjr.sjr_score, 5) AS sjr_score,
    Round(rolap.ais.ais_score, 5) AS ais_score,
    Round(rolap.snip.snip_score, 5) AS snip_score,
    SortedClusters.clusters
  FROM rolap.journal_names
  INNER JOIN rolap.active_journals
    ON active_journals.id = journal_names.id
  LEFT JOIN rolap.impact_factor2
    ON impact_factor2.journal_id = journal_names.id
  LEFT JOIN rolap.impact_factor5
    ON impact_factor5.journal_id = journal_names.id
  LEFT JOIN rolap.journal_h5
    ON journal_h5.journal_id = journal_names.id
  LEFT JOIN rolap.eigenfactor
    ON eigenfactor.journal_id = journal_names.id
  LEFT JOIN rolap.sjr
    ON sjr.journal_id = journal_names.id
  LEFT JOIN rolap.ais
    ON ais.journal_id = journal_names.id
  LEFT JOIN rolap.snip
    ON snip.journal_id = journal_names.id
  -- Pre-calculate clusters with correct ordering
  LEFT JOIN (
    SELECT journal_id, Group_concat(community_id, '-') AS clusters
    FROM (
        SELECT journal_id, community_id 
        FROM rolap.journal_communities 
        ORDER BY community_id ASC
    )
    GROUP BY journal_id
  ) AS SortedClusters
    ON SortedClusters.journal_id = journal_names.id
  ORDER BY title;
