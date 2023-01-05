-- Create table linking citable works to single ISSN

CREATE TABLE rolap.works_issn AS
  SELECT id, doi,
    Coalesce(issn_print, issn_electronic) AS issn, published_year
  FROM works
  WHERE issn is not null
    -- To avoid news articles, book reviews, etc. include works longer than
    -- two pages
    AND Substr(page, Instr(page, "-") + 1)
      - Substr(page, 0, Instr(page, "-")) > 1;
