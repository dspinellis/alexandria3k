-- Wrapper to run SNIP calculation via CLI options
.backup ././test_snip.db
.shell ./snip.py --db ././test_snip.db --rolap-db ././test_snip.db
.restore ././test_snip.db
.shell rm ././test_snip.db