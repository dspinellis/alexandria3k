-- Global two-year impact factor

SELECT two_year_citations.year,
  Cast(citations_number AS float) / (past_y1_works.n + past_y2_works.n)
    AS impact_factor
  FROM rolap.two_year_citations
  INNER JOIN rolap.yearly_works_all as past_y1_works
    ON past_y1_works.published_year = two_year_citations.year - 1
  INNER JOIN rolap.yearly_works_all as past_y2_works
    ON past_y2_works.published_year = two_year_citations.year - 2;
