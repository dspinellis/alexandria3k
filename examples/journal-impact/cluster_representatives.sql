-- Top-ten (by 5y impact factor) representative journals for each cluster

CREATE INDEX IF NOT EXISTS rolap.journal_communities_journal_id_idx
  ON journal_communities(journal_id);

CREATE INDEX rolap.journal_communities_journal_id_community_id_idx
  ON journal_communities (journal_id, community_id);

CREATE INDEX rolap.citation_mean_2y_journal_id_idx
  ON citation_mean_2y (journal_id);

CREATE TABLE rolap.cluster_representatives AS
  WITH monothematic_journals AS (
    SELECT community_id, journal_id
      FROM rolap.journal_communities 
      GROUP BY journal_id
      HAVING Count(*) = 1
  ),
  ranked_journals AS (
    SELECT community_id, journal_id,
      Row_number() OVER (
        PARTITION BY community_id ORDER BY citations_number DESC
      ) AS row_rank
      FROM monothematic_journals
      LEFT JOIN rolap.citation_mean_2y USING(journal_id)
  )
  SELECT * from ranked_journals
    WHERE row_rank <= 10;
