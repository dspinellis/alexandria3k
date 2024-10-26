-- Create table of citable works: those longer than two pages

CREATE TABLE rolap.citable_works AS
  SELECT * FROM rolap.works_issn
  WHERE
    -- To avoid news articles, book reviews, etc. include works longer than
    -- two pages
    page is null
      OR Instr(page, '-') = 0
      OR Substr(page, Instr(page, '-') + 1)
        - Substr(page, 0, Instr(page, '-')) > 1
    ;
