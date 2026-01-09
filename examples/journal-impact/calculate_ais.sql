-- Wrapper to run AIS calculation via CLI options
.backup ././test_ais.db
.shell ./eigenfactor.py --metric ais --db ././test_ais.db --rolap-db ././test_ais.db
.restore ././test_ais.db
.shell rm ././test_ais.db