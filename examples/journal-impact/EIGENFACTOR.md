# Eigenfactor Score Calculation

This directory contains the implementation for calculating [Eigenfactor scores](http://www.eigenfactor.org/methods.pdf) for journals in the Alexandria3k database. The Eigenfactor score is a measure of the total importance of a scientific journal, similar to Google's PageRank algorithm, but applied to the citation network.

## Overview

The calculation involves the following steps:
1.  **Data Preparation**: Aggregating citation data and article counts from the main database into optimized intermediate tables.
2.  **Score Calculation**: A Python script (`eigenfactor.py`) reads the aggregated data, constructs a sparse adjacency matrix of the citation network, and computes the principal eigenvector using the power iteration method.
3.  **Reporting**: The calculated scores are stored in the database and can be joined with other metrics (like Impact Factor) for reporting.

## Files

*   `eigenfactor.py`: The main Python script that performs the matrix computations.
*   `citation_network.sql`: SQL script to aggregate citation counts between journals (Adjacency Matrix).
*   `eigenfactor.sql`: SQL script to define the schema for the results table.
*   `test_eigenfactor.py`: Unit tests for the Python script.

## Prerequisites

*   A populated Alexandria3k database (ROLAP schema).
*   Python 3.13.9 or higher.
*   [uv](https://github.com/astral-sh/uv) package manager.

## Installation

This project uses `uv` for dependency management. To set up the environment:

```bash
# Install dependencies
uv sync

# Activate the virtual environment (optional, uv runs commands in the env automatically)
# On Windows:
.venv\Scripts\activate
# On Unix:
source .venv/bin/activate
```

## Step-by-Step Guide

### 1. Prepare Intermediate Tables

Before running the Python script, you must create the necessary intermediate tables in the `rolap` database. These tables speed up the calculation by pre-aggregating the data.

Run the following SQL scripts against your `impact` and `rolap` databases:

```bash
make
```


### 2. Run the Calculation

Execute the Python script to calculate the scores. You can configure the database paths using environment variables if they differ from the defaults (`impact` and `rolap`).

```bash
# Default usage (assumes impact.db and rolap.db in current directory or /tmp)
uv run eigenfactor.py

# Custom database paths
export MAINDB=/path/to/impact
export ROLAPDB=/path/to/rolap
uv run eigenfactor.py
```

The script will:
1.  Load the article counts and citation network from the SQL tables.
2.  Construct the sparse matrix.
3.  Run the power iteration algorithm until convergence.
4.  Save the resulting scores to the `rolap.eigenfactor` table.

### 3. Generate Reports

Once the scores are calculated, you can generate the full journal impact report, which now includes the Eigenfactor score.

```bash
make
```

## Testing

### Unit Tests
The Python logic is tested using `pytest`. The tests cover various graph topologies (rings, dangling nodes, disconnected components) to ensure the algorithm behaves correctly.

```bash
uv run pytest test_eigenfactor.py
```

### Database Tests
The SQL logic is tested using `.rdbu` files (Relational Database Unit tests).

*   `article_counts.rdbu`
*   `citation_network.rdbu`

You can run these using the project's test infrastructure (e.g., `make test`).
