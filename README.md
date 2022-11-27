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

## Command line execution
```sh
pipenv shell
cd alexandria3k
# Obtain list of command-line options
./alexandria3k.py --help
```

### Command-line options
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

## Database schema
The complete schema of a populated database appears below.
Direct queries can be performed only on the Crossref data set.
![Database schema](./schema.svg)
<img src="./schema.svg">

## Name
The _alexandria3k_ package is named after the
[Library of Alexandria](https://en.wikipedia.org/wiki/Library_of_Alexandria),
indicating how publication data can be processed in the third millenium AD.
