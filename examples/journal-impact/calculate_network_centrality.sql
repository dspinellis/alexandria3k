-- Wrapper to run Journal Network Centrality calculation via CLI options
-- Generic metric; resembles Eigenfactor
.backup ././test_jnc.db
.shell ./journal_network_metrics.py --metric network_centrality --db ././test_jnc.db --rolap-db ././test_jnc.db
.restore ././test_jnc.db
.shell rm ././test_jnc.db