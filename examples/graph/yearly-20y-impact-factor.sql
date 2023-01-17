-- Global twenty-year impact factor

SELECT twenty_year_citations.year,
  Cast(citations_number AS float) / twenty_year_publications.n AS impact_factor
  FROM rolap.twenty_year_citations
  INNER JOIN rolap.twenty_year_publications
    ON twenty_year_publications.year = twenty_year_citations.year;
