-- Wrapper to run Prestige Weighted Rank calculation via CLI options
-- Generic metric; resembles the SCImago Journal Rank (SJR) metric
.backup ././test_pwr.db
.shell ./journal_network_metrics.py --metric prestige_rank --db ././test_pwr.db --rolap-db ././test_pwr.db
.restore ././test_pwr.db
.shell rm ././test_pwr.db