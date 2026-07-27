-- The final report of journal impact metrics
-- with nonsensical values filtered out

.mode csv
.headers on

SELECT
    title AS 'Journal Title',
    Publisher,
    CASE
        WHEN issn_print != ''
        THEN '<a href="https://portal.issn.org/resource/ISSN/' ||
          issn_print || '">' ||
          substr(issn_print, 1, 4) || '-' || substr(issn_print, 5, 4) ||
          ' (p)</a> '
        ELSE ''
    END ||
    CASE
        WHEN issn_eprint != ''
        THEN '<a href="https://portal.issn.org/resource/ISSN/' ||
          issn_eprint || '">' ||
          substr(issn_eprint, 1, 4) || '-' || substr(issn_eprint, 5, 4) ||
          ' (e)</a> '
        ELSE ''
    END ||
    CASE
        WHEN issns_additional != ''
        THEN '[' || issns_additional || '] (a) '
        ELSE ''
    END AS ISSNs,
    CASE
      WHEN doi != ''
      THEN '<a href="https://doi.org/' || doi || '">' || doi || '</a>'
      ELSE ''
    END AS DOI,
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
    Coalesce(cluster_weights, Replace(clusters, '-', ', ')) AS Clusters
  FROM rolap.journal_impact ORDER BY title;
