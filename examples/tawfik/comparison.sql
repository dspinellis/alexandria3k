-- Compare the CD index of each D. Tawfik work with the baseline
-- for that journal and year

CREATE TABLE rolap.comparison AS
  SELECT doi, tawfik_cdindex.cdindex AS t_cd5,
      baseline_cdindex.cdindex AS b_cd5
    FROM rolap.baseline_cdindex
    INNER JOIN rolap.tawfik_cdindex ON
      Cast(tawfik_cdindex.published_year AS integer)
          = baseline_cdindex.published_year
        AND tawfik_cdindex.issn_print = baseline_cdindex.issn_print
    WHERE baseline_cdindex.issn_print is not null
      AND baseline_cdindex.published_year <= 2016;
