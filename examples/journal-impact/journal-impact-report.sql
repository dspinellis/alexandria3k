-- Create a CSV file with the calculated journal impact metrics.

CREATE INDEX IF NOT EXISTS rolap.citation_mean_2y_idx ON citation_mean_2y(journal_id);
CREATE INDEX IF NOT EXISTS rolap.citation_mean_5y_idx ON citation_mean_5y(journal_id);
CREATE INDEX IF NOT EXISTS rolap.journal_h5_idx ON journal_h5(journal_id);
CREATE INDEX IF NOT EXISTS rolap.network_centrality_idx ON network_centrality(journal_id);
CREATE INDEX IF NOT EXISTS rolap.prestige_rank_idx ON prestige_rank(journal_id);
CREATE INDEX IF NOT EXISTS rolap.mean_article_score_idx ON mean_article_score(journal_id);
CREATE INDEX IF NOT EXISTS rolap.context_impact_idx ON context_impact(journal_id);
CREATE INDEX IF NOT EXISTS rolap.journal_communities_idx ON journal_communities(journal_id);

.mode csv
.headers on

SELECT
    rolap.journal_names.title,
    rolap.journal_names.publisher,
    rolap.journal_names.issn_print,
    rolap.journal_names.issn_eprint,
    rolap.journal_names.issns_additional,
    rolap.journal_names.doi,
    -- 2-Year Metrics
    rolap.citation_mean_2y.citations_number AS citations_number2,
    rolap.citation_mean_2y.publications_number AS publications_number2,
    Round(rolap.citation_mean_2y.citation_mean, 2) AS citation_mean_2y,
    -- 5-Year Metrics
    rolap.citation_mean_5y.citations_number AS citations_number5,
    rolap.citation_mean_5y.publications_number AS publications_number5,
    Round(rolap.citation_mean_5y.citation_mean, 2) AS citation_mean_5y,
    -- h-index Metrics
    rolap.journal_h5.h5_index,
    rolap.journal_h5.h5_median,
    -- Network Centrality Metrics
    Round(rolap.network_centrality.centrality_score, 5) AS network_centrality,
    Round(rolap.prestige_rank.prestige_score, 5) AS prestige_rank,
    Round(rolap.mean_article_score.mean_score, 5) AS mean_article_score,
    Round(rolap.context_impact.impact_score, 5) AS context_impact,
    -- Clusters
    SortedClusters.clusters
  FROM rolap.journal_names
  INNER JOIN rolap.active_journals
    ON active_journals.id = journal_names.id
  LEFT JOIN rolap.citation_mean_2y
    ON citation_mean_2y.journal_id = journal_names.id
  LEFT JOIN rolap.citation_mean_5y
    ON citation_mean_5y.journal_id = journal_names.id
  LEFT JOIN rolap.journal_h5
    ON journal_h5.journal_id = journal_names.id
  LEFT JOIN rolap.network_centrality
    ON network_centrality.journal_id = journal_names.id
  LEFT JOIN rolap.prestige_rank
    ON prestige_rank.journal_id = journal_names.id
  LEFT JOIN rolap.mean_article_score
    ON mean_article_score.journal_id = journal_names.id
  LEFT JOIN rolap.context_impact
    ON context_impact.journal_id = journal_names.id
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
