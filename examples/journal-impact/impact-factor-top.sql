-- Impact factor of all journals

SELECT * FROM rolap.impact_factor_titles
  ORDER BY impact_factor DESC
  LIMIT 100;
