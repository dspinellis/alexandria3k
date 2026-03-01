-- Wrapper to run Mean Article Network Score calculation via CLI options
-- Generic metric; resembles the Article Influence Score (AIS) metric
.backup ././test_mans.db
.shell ./journal_network_metrics.py --metric mean_article_score --db ././test_mans.db --rolap-db ././test_mans.db
.restore ././test_mans.db
.shell rm ././test_mans.db