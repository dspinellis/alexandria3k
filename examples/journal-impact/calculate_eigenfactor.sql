-- Wrapper to run Eigenfactor calculation via CLI options
.backup ././test_ef.db
.shell ./eigenfactor.py --metric eigenfactor --db ././test_ef.db --rolap-db ././test_ef.db
.restore ././test_ef.db
.shell rm ././test_ef.db