-- Produce community and titles of representative journals

SELECT community_id, Group_concat(journal_names.title, ', ')
  FROM rolap.cluster_representatives
  LEFT JOIN journal_names
    ON cluster_representatives.journal_id = journal_names.id
  GROUP BY community_id
  ORDER BY community_id, row_rank;
