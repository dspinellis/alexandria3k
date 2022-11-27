## Alexandria3k

The _alexandria3k_ package
supplies a library and a command-line tool providing efficient relational query
access the entire
[Crossref dataset](https://www.nature.com/articles/d41586-022-02926-y)
(157 GB compressed, 1 PB uncompressed).
This contains publication metadata from about 134 million publications from
all major international publishers with full citation data for 60 million
of them.
The _alexandria3k_ package installation contains all elements required
to run it.
It does not require the installation, configuration, and maintenance
of a third party relational or graph database.
It can therefore be used out-of-the-box for performing reproducible
publication research on the desktop.

The Crossref dataset can be linked with:
* the [ORCID summary dataset](https://support.orcid.org/hc/en-us/articles/360006897394-How-do-I-get-the-public-data-file-)
  (25 GB compressed, 435 GB uuncompressed),
  containing about 15 million author records, and
* the funder dataset

## Installation
Currently _alexandria3k_ is considered early-beta quality,
and is therefore installed and used through this repository,
rather than as a Python package.

```sh
git clone https://github.com/dspinellis/alexandria3k.git
cd alexandra3k/src
pipenv install
```

## Data downloading

### Crossref data
The main data set on which _alexandria3k_ operates is that
of [Crossref](https://www.crossref.org), comprising about 130 million
publication metadata records with more than 1.7 billion reference
records and 359 million author records.
You can obtain the data from
[Acedemic Torrents](https://academictorrents.com/browse.php?search=crossref)
using a torrent client of your choice.
Below is an example of commands that download the April 2022 snapshot
(the one on which _alexandria3k_ has been tested).

```sh
# Download Crossref torrent file
wget https://doi.org/10.13003/83b2gq

# Download Crossref data (168 GB) through the torrent
aria2c 83b2gq
```

### ORCID data
You can populate a database with data regarding authors (URLs, countries,
external identifiers, education, employment, etc.) from the
[ORCID](https://orcid.org/) initiative.
For this you need to download the _summary file_
of the ORCID Public Data File (e.g. `ORCID_2022_10_summaries.tar.gz` — 25GB)
through [Figshare](https://orcid.figshare.com/).
Note that _alexandria3k_ works on the compressed file;
there is no need to expand it (it expands to about 0.5 PB).

### Other data sources
The _alexandria3k_ system can also add to a database the following
tables.
You can download the data and point _alexandria3k_ to the corresponding file,
or, because the data sets are relatively small, you can provide _alexandria3k_
the URL from which it will directly stream the data to populate the database.

* [Crossref journal data](http://ftp.crossref.org/titlelist/titleFile.csv)
* [Crossref funder data](https://doi.crossref.org/funderNames?mode=list)
* [Open access journal metadata](https://doaj.org/csv) from the [https://doaj.org/](directory of open access journals)

## Use overview
After downloading the Crossref data you can use _alexandria3k_ through its
Python API or as a command-line tool.
These are the things you can do with _alexandria3k_.

* Directly run ad hoc SQL queries on the Crossref data
* Populate SQLite databases with Crossref, ORCID, DOAJ, and other data
  * Select a horizontal subset of Crossref records
    * Through an SQL expression
    * By sampling a subset of the 26 thousand containers in the dataset
  * Select a vertical subset of columns
    * Using the `Table.Column` or `Table.*` notation

Populating a database can take
minutes (for a small, e.g. experimental, subset),
a few hours (to traverse the whole Crossref dataset and obtain a few thousands
of records),
or a couple of days (to produce a large set, e.g. by selecting some columns).

After your populate an SQLite database and create suitable indexes,
SQL queries often run in seconds.

## Relational schema
The complete schema of a fully-populated database appears below.
(Follow the linked image to the "Raw" file to see it in full size.)
Direct SQL queries can also be performed on the Crossref data set.

![Database schema](./schema.svg)

Queries involving multiple scans of the tables (e.g. relational joins)
should be performed by directing _alexandria3k_ to perform them separately
in each partition.
This however means that aggregation operations will not work as expected,
because they will be run multiple times (once for every partition).

## Command line execution

### Preparation
```sh
# While in alexandria3k/src directory

# Launch a shell in the virtual environment
pipenv shell

# Navigate to the source code directory
cd alexandria3k
```

### Obtain list of command-line options
```sh
alexandria3k.py --help
```

### Show DOI ond title of all publications
```sh
alexandria3k.py --crossref-directory 'April 2022 Public Data File from Crossref'  \
   --query 'SELECT DOI, title FROM works' >doi-title.csv
```

### Count Crossref publications by year and type
This query performs a single pass through the data set to obtain
the number of Crossref publications by year and publication type.
```sh
alexandria3k --crossref-directory 'April 2022 Public Data File from Crossref' \
   --query '
```
```sql
WITH counts AS (
  SELECT
    published_year AS year,
    type,
    Count(*) AS number
FROM   works
    GROUP by published_year, type)

SELECT year AS name, Sum(number) FROM counts
  GROUP BY year
UNION
SELECT type AS name, Sum(number) FROM counts
  GROUP BY type' >results.csv
```

### Sampling
The following command counts the number of publication that have
or do not have an abstract in a 1% sample of the data set's containers.
It runs in a couple of minutes, rather than hours.
```sh
alexandria3k.py --crossref-directory 'April 2022 Public Data File from Crossref'  \
   --sample 'random.random() < 0.01' \
   --query '
```
```sql
'SELECT works.abstract is not null AS have_abstract, Count(*)
  FROM works GROUP BY have_abstract'
```

### Database of COVID research
The following command creates an SQLite database with all Crossref data
regarding publications that contain "COVID" in their title or abstract.
```sh
alexandria3k.py --crossref-directory 'April 2022 Public Data File from Crossref' \
   --populate-db-path covid.db \
   --row-selection "title like '%COVID%' OR abstract like '%COVID%' "
```

### Publications graph
The following command selects only a subset of columns of the complete
Crossref data set to create a navigable graph between publications and
their references.
```sh
alexandria3k.py --crossref-directory 'April 2022 Public Data File from Crossref' \
   --populate-db-path graph.db \
   --columns works.doi work_references.work_id work_references.doi work_funders.id \
    work_funders.work_id work_funders.doi funder_awards.funder_id funder_awards.name \
    author_affiliations.author_id author_affiliations.name work_subjects.work_id work_subjects.name \
    work_authors.id work_authors.work_id work_authors.orcid
```

Through this data set you can run on the database queries such as the following.
```sql
SELECT COUNT(*) FROM works;
SELECT COUNT(*) FROM (SELECT DISTINCT work_id FROM works_subjects);
SELECT COUNT(*) FROM (SELECT DISTINCT work_id FROM work_references);
SELECT COUNT(*) FROM affiliations_works;
SELECT COUNT(*) FROM (SELECT DISTINCT work_id FROM work_funders);

SELECT COUNT(*) FROM work_authors;
SELECT COUNT(*) FROM work_authors WHERE orcid is not null;
SELECT COUNT(*) FROM (SELECT DISTINCT orcid FROM work_authors);

SELECT COUNT(*) FROM authors_affiliations;
SELECT COUNT(*) FROM affiliation_names;

SELECT COUNT(*) FROM works_subjects;
SELECT COUNT(*) FROM subject_names;

SELECT COUNT(*) FROM work_funders;
SELECT COUNT(*) FROM funder_awards;

SELECT COUNT(*) FROM work_references;
```

## Command-line options reference
<!-- CLI start -->
```
usage: alexandria3k.py [-h] [-C CROSSREF_DIRECTORY] [-c COLUMNS [COLUMNS ...]]
                       [-D DEBUG [DEBUG ...]] [-A [OPEN_ACCESS_JOURNALS]]
                       [-E OUTPUT_ENCODING] [-F FIELD_SEPARATOR]
                       [-i [INDEX ...]] [-J [JOURNAL_NAMES]] [-L] [-l] [-n]
                       [-O ORCID_DATA] [-o OUTPUT] [-P] [-p POPULATE_DB_PATH]
                       [-Q QUERY_FILE] [-q QUERY] [-R ROW_SELECTION_FILE]
                       [-r ROW_SELECTION] [-s SAMPLE] [-U [FUNDER_NAMES]]

alexandria3k: Publication metadata interface

optional arguments:
  -h, --help            show this help message and exit
  -C CROSSREF_DIRECTORY, --crossref-directory CROSSREF_DIRECTORY
                        Directory storing the downloaded Crossref publication
                        data
  -c COLUMNS [COLUMNS ...], --columns COLUMNS [COLUMNS ...]
                        Columns to populate using table.column or table.*
  -D DEBUG [DEBUG ...], --debug DEBUG [DEBUG ...]
                        Output debuggging information as specfied by the
                        arguments. files-read: Output counts of data files
                        read; log-sql: Output executed SQL statements; perf:
                        Output performance timings; populated-counts: Dump
                        counts of the populated database; populated-data: Dump
                        the data of the populated database; populated-reports:
                        Output query results from the populated database;
                        progress: Report progress; stderr: Log to standard
                        error; virtual-counts: Dump counts of the virtual
                        database; virtual-data: Dump the data of the virtual
                        database.
  -A [OPEN_ACCESS_JOURNALS], --open-access-journals [OPEN_ACCESS_JOURNALS]
                        Populate database with DOAJ open access journal
                        metadata from URL or file
  -E OUTPUT_ENCODING, --output-encoding OUTPUT_ENCODING
                        Query output character encoding (use utf-8-sig for
                        Excel)
  -F FIELD_SEPARATOR, --field-separator FIELD_SEPARATOR
                        Character to use for separating query output fields
  -i [INDEX ...], --index [INDEX ...]
                        SQL expressions that select the populated rows
  -J [JOURNAL_NAMES], --journal-names [JOURNAL_NAMES]
                        Populate database with Crossref journal names from URL
                        or file
  -L, --list-schema     List the schema of the scanned database
  -l, --linked-records  Only add ORCID records that link to existing ones
  -n, --normalize       Normalize relations in the populated Crossref database
  -O ORCID_DATA, --orcid-data ORCID_DATA
                        URL or file for obtaining ORCID author data
  -o OUTPUT, --output OUTPUT
                        Output file for query results
  -P, --partition       Run the query over partitioned data slices. (Warning:
                        arguments are run per partition.)
  -p POPULATE_DB_PATH, --populate-db-path POPULATE_DB_PATH
                        Populate the SQLite database in the specified path
  -Q QUERY_FILE, --query-file QUERY_FILE
                        File containing query to run on the virtual tables
  -q QUERY, --query QUERY
                        Query to run on the virtual tables
  -R ROW_SELECTION_FILE, --row-selection-file ROW_SELECTION_FILE
                        File containing SQL expression that selects the
                        populated rows
  -r ROW_SELECTION, --row-selection ROW_SELECTION
                        SQL expression that selects the populated rows
  -s SAMPLE, --sample SAMPLE
                        Python expression to sample the Crossref tables (e.g.
                        random.random() < 0.0002)
  -U [FUNDER_NAMES], --funder-names [FUNDER_NAMES]
                        Populate database with Crossref funder names from URL
                        or file
```
<!-- CLI end -->

## Python API
Coming soon.

## Name
The _alexandria3k_ package is named after the
[Library of Alexandria](https://en.wikipedia.org/wiki/Library_of_Alexandria),
indicating how publication data can be processed in the third millenium AD.
