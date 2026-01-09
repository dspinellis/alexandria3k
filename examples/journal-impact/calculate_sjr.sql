-- Wrapper to run SJR calculation via CLI options
.backup ././test_sjr.db
.shell ./eigenfactor.py --metric sjr --db ././test_sjr.db --rolap-db ././test_sjr.db
.restore ././test_sjr.db
.shell rm ././test_sjr.db