-- Wrapper to run Context Normalized Impact calculation via CLI options
-- Generic metric; resembles the Source Normalized Impact per Paper (SNIP) metric
.backup ././test_cni.db
.shell ./context_normalized_impact.py --db ././test_cni.db --rolap-db ././test_cni.db
.restore ././test_cni.db
.shell rm ././test_cni.db