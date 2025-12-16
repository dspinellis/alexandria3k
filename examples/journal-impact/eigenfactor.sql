-- Create the Eigenfactor score table
--
-- This script defines the schema for the `rolap.eigenfactor` table, which will store
-- the final calculated scores. It is populated by the `eigenfactor.py` Python script.
--
-- Note: The actual scores are calculated and populated by eigenfactor.py

CREATE TABLE IF NOT EXISTS rolap.eigenfactor (
  journal_id INTEGER PRIMARY KEY,
  eigenfactor_score REAL
);