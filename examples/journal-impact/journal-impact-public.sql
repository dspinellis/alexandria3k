-- The final report of journal impact metrics
-- with nonsensical values filtered out

.mode csv
.headers on

SELECT
    title AS 'Journal Title',
    Publisher,
    issn_print AS 'Print ISSN',
    issn_eprint AS 'E-Print ISSN',
    issns_additional AS 'Additional ISSN',
    DOI,
    citations_number2 AS '2-Year Citations',
    publications_number2 AS '2-Year Publications',
    CASE
        WHEN publications_number2 >= 25
        THEN citation_mean_2y
        ELSE NULL
    END AS '2-Year Mean Citations',
    citations_number5 AS '5-Year Citations',
    publications_number5 AS '5-Year Publications',
    CASE
        WHEN publications_number5 >= 50
        THEN citation_mean_5y
        ELSE NULL
    END AS '5-Year Mean Citations',
    CASE
        WHEN publications_number5 >= 50
        THEN h5_index
        ELSE NULL
    END AS 'h5-Index',
    CASE
        WHEN publications_number5 >= 50
        THEN h5_median
        ELSE NULL
    END AS 'h5-Median',
    CASE
      WHEN publications_number5 >= 25
           AND citations_number5 > 0
      THEN network_centrality
      ELSE NULL
    END AS 'Network Centrality',
    CASE
      WHEN publications_number5 >= 25
           AND citations_number5 >= 5
      THEN prestige_rank
      ELSE NULL
    END AS 'Prestige Rank',
    CASE
      WHEN publications_number5 >= 50
           AND citations_number5 >= 10
      THEN mean_article_score
      ELSE NULL
    END AS 'Mean Article Score',
    CASE
      WHEN publications_number5 >= 25
           AND citations_number5 >= 5
      THEN context_impact
      ELSE NULL
    END AS 'Context Impact',
    Coalesce(cluster_labels, cluster_weights, Replace(clusters, '-', ', ')) AS Clusters
  FROM rolap.journal_impact ORDER BY title;
