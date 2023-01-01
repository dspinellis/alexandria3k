
.print Covered citing percentage
SELECT
  Cast((SELECT Sum(citing_citations_number)
    FROM subject_hierarchy) AS FLOAT) /
  (SELECT Sum(citations_number)
    FROM subject_hierarchy
    LEFT JOIN work_subject_citations
      ON subject_hierarchy.citing_subject_id
        = work_subject_citations.citing_subject_id) * 100;

.print Covered cited percentage
SELECT
  Cast((SELECT Sum(cited_citations_number)
    FROM subject_hierarchy) AS FLOAT) /
  (SELECT Sum(citations_number)
    FROM subject_hierarchy
    LEFT JOIN work_subject_citations
      ON subject_hierarchy.cited_subject_id
        = work_subject_citations.cited_subject_id) * 100;
