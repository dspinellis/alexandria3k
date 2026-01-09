#!/usr/bin/env python
#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2025  Panagiotis Spanakis
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""
Calculate network centrality metrics (Journal Network Centrality, Prestige Weighted Rank,
or Mean Article Network Score) for journals in the Alexandria3k database.

This script calculates three variations of eigenvector centrality:
- **Journal Network Centrality**: Measures total influence based on a 5-year citation
  window, excluding self-citations. (Resembles Eigenfactor score). 
- **Prestige Weighted Rank**: Measures prestige per article based on a 3-year citation
  window, limiting self-citations to 33%. (Resembles SCImago Journal Rank / SJR).
- **Mean Article Network Score**: Measures average influence per article based on a
  5-year citation window, excluding self-citations. (Resembles Article Influence Score / AIS).

All metrics use the power iteration method on the sparse adjacency matrix
to compute eigenvector centrality.

Usage:
    ./eigenfactor.py                    # Calculate Journal Network Centrality (default)
    ./eigenfactor.py --metric eigenfactor  # Calculate Journal Network Centrality
    ./eigenfactor.py --metric sjr       # Calculate Prestige Weighted Rank
    ./eigenfactor.py --metric ais       # Calculate Mean Article Network Score

Key differences between metrics:
- Journal Network Centrality: 5-year window, removes self-citations, sums to 100%
- Prestige Weighted Rank: 3-year window, limits self-citations to 33%, per-article normalization
- Mean Article Network Score: 5-year window, removes self-citations, per-article normalization (mean=1.0)

Environment Variables:
    MAINDB: Path to the main database (without .db extension). Default: 'impact'
    ROLAPDB: Path to the ROLAP database (without .db extension). Default: 'rolap'
"""

import argparse
import os
import itertools
import sqlite3
import logging
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix, diags

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Constants
ALPHA = 0.85
EPSILON = 1e-6
MAX_ITER = 1000
MAX_SELF_CITATION_RATIO = 0.33  # SJR limits self-citations to 33%


def get_db_connection(db_path, rolap_db_path):
    """
    Establish connection to the main database and attach the ROLAP database.
    """
    if not os.path.exists(db_path):
        logging.critical(f"Main database file '{db_path}' not found.")
        raise FileNotFoundError(f"Database file '{db_path}' not found.")

    logging.info(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)

    if not os.path.exists(rolap_db_path):
        logging.critical(f"ROLAP database file '{rolap_db_path}' not found.")
        raise FileNotFoundError(f"Database file '{rolap_db_path}' not found.")

    logging.info(f"Attaching {rolap_db_path} as rolap...")
    conn.execute(f"ATTACH DATABASE '{rolap_db_path}' AS rolap")

    return conn


def load_data(conn, metric="eigenfactor"):
    """
    Load citation network and article counts from the database.

    Args:
        conn: Database connection
        metric: "eigenfactor" or "ais" (5-year window) or "sjr" (3-year window)

    Returns:
        tuple: (citations_df, journal_article_counts)
    """
    if metric == "sjr":
        publications_table = "publications3"
        citation_table = "citation_network3"
        window_years = 3
    else:
        # Both Eigenfactor and AIS use 5-year window
        publications_table = "publications5"
        citation_table = "citation_network"
        window_years = 5

    # 1. Get Article Counts (Article Vector)
    logging.info(f"Fetching article counts ({window_years}-year window)...")

    article_query = f"""
        SELECT journal_id, publications_number AS article_count
        FROM rolap.{publications_table}
    """
    articles_df = pd.read_sql_query(article_query, conn)

    journal_article_counts = dict(
        zip(articles_df["journal_id"], articles_df["article_count"])
    )
    logging.info(f"Found {len(journal_article_counts)} journals with citable works.")

    # 2. Get Citation Network
    logging.info(f"Fetching citation network ({window_years}-year window)...")
    citation_query = f"""
        SELECT
          citing_journal,
          cited_journal,
          citation_count
        FROM rolap.{citation_table}
    """
    try:
        citations_df = pd.read_sql_query(citation_query, conn)
        logging.info(f"Found {len(citations_df)} citation links.")
    except Exception as e:
        logging.critical(f"Error reading rolap.{citation_table}: {e}")

    return citations_df, journal_article_counts


def calculate_metric(
    citations_df,
    journal_article_counts,
    metric="eigenfactor",
    alpha=ALPHA,
    epsilon=EPSILON,
    max_iter=MAX_ITER,
    max_self_citation_ratio=MAX_SELF_CITATION_RATIO,
):
    """
    Calculate journal network centrality metric using sparse matrices.

    The algorithm proceeds in several steps:
    1.  **Matrix Construction**: Builds a sparse adjacency matrix (Z) from the citation dataframe.
        Z[i, j] represents citations from journal i to journal j.

    2.  **Self-Citation Handling**:
        - Journal Network Centrality/Mean Article Network Score: Removes self-citations entirely (diagonal = 0)
        - Prestige Weighted Rank: Limits self-citations to 33% of incoming citations

    3.  **Column Normalization**: Transposes Z to get H (citations from j to i) and normalizes
        the columns to make the matrix column-stochastic (sum of each column = 1).

    4.  **Article Vector**: Creates a normalized vector of article counts. This vector is used
        to redistribute the probability mass from "dangling nodes".

    5.  **Power Iteration**: Iteratively computes the principal eigenvector (pi) of the
        modified Google Matrix.

    6.  **Score Calculation**:
        - Journal Network Centrality (resembles Eigenfactor): 100 * (H * pi), normalized to sum to 100%
        - Prestige Weighted Rank (resembles SJR): Per-article prestige, normalized so mean = 1.0
        - Mean Article Network Score (resembles AIS): Per-article prestige, normalized so mean = 1.0

    Args:
        citations_df (pd.DataFrame): DataFrame containing 'citing_journal', 'cited_journal', 'citation_count'.
        journal_article_counts (dict): Dictionary mapping journal_id to article count.
        metric (str): "eigenfactor", "sjr", or "ais".
        alpha (float): Damping factor (default 0.85).
        epsilon (float): Convergence threshold.
        max_iter (int): Maximum number of iterations.
        max_self_citation_ratio (float): Maximum ratio of self-citations for SJR (default 0.33).

    Returns:
        pd.DataFrame: DataFrame with 'journal_id' and score column.
    """
    score_columns = {
        "eigenfactor": "eigenfactor_score",
        "sjr": "sjr_score",
        "ais": "ais_score",
    }
    score_column = score_columns.get(metric, "eigenfactor_score")

    # Identify all journals involved (citing or cited)
    journals = sorted(
        list(
            set(citations_df["citing_journal"]).union(
                set(citations_df["cited_journal"])
            )
        )
    )
    journal_to_idx = {journal: i for i, journal in enumerate(journals)}
    n = len(journals)

    if n == 0:
        return pd.DataFrame(columns=["journal_id", score_column])

    logging.info(f"Constructing sparse matrix for {n} journals...")

    # Map journal IDs to matrix indices
    citing_indices = citations_df["citing_journal"].map(journal_to_idx).values
    cited_indices = citations_df["cited_journal"].map(journal_to_idx).values
    counts = citations_df["citation_count"].values.astype(np.float32)

    # Create sparse matrix Z (citations FROM citing TO cited)
    # Z[i, j] = citations from journal i to journal j
    Z = csr_matrix(
        (counts, (citing_indices, cited_indices)), shape=(n, n), dtype=np.float32
    )

    # Transpose to get H (citations FROM j TO i) for column-stochastic formulation
    # H[i, j] is proportional to probability of moving from j to i
    H = Z.T.tocsr()

    # Handle self-citations based on metric type
    if metric in ("eigenfactor", "ais"):
        # Eigenfactor/AIS: Remove self-citations entirely
        H.setdiag(0)
        H.eliminate_zeros()
    else:
        # SJR: Limit self-citations to max 33% of incoming citations per journal
        logging.info("Limiting self-citations to 33% of incoming citations...")
        H_lil = H.tolil()
        for j in range(n):
            col_sum = H[:, j].sum()
            if col_sum > 0:
                self_citation = H_lil[j, j]
                max_allowed = col_sum * max_self_citation_ratio
                if self_citation > max_allowed:
                    H_lil[j, j] = max_allowed
        H = H_lil.tocsr()

    # Create Article Vector (a)
    # Normalized vector of article counts
    article_counts_arr = np.array(
        [journal_article_counts.get(j, 0) for j in journals], dtype=np.float32
    )
    total_articles = article_counts_arr.sum()

    if total_articles > 0:
        article_vector = article_counts_arr / total_articles
    else:
        logging.warning("Total article count is 0. Using uniform distribution.")
        article_vector = np.ones(n, dtype=np.float32) / n

    # Normalize H columns (make it column-stochastic)
    column_sums = np.array(H.sum(axis=0)).flatten()
    dangling_mask = column_sums == 0
    non_zero_mask = column_sums > 0

    if np.any(non_zero_mask):
        inv_col_sums = np.zeros(n, dtype=np.float32)
        inv_col_sums[non_zero_mask] = 1.0 / column_sums[non_zero_mask]
        D_inv = diags(inv_col_sums, format="csr")
        H = H @ D_inv

    # Power Iteration
    logging.info("Starting power iteration...")
    pi = np.ones(n, dtype=np.float32) / n

    for iteration in range(max_iter):
        # Calculate influence from dangling nodes
        dangling_sum = pi[dangling_mask].sum() if np.any(dangling_mask) else 0.0

        # H @ pi: flow through links
        pi_new = alpha * (H @ pi)

        # Teleportation + Dangling nodes
        teleport_factor = alpha * dangling_sum + (1 - alpha)
        pi_new += teleport_factor * article_vector

        # Check convergence (L1 norm)
        diff = np.linalg.norm(pi_new - pi, ord=1)
        if diff < epsilon:
            logging.info(f"Converged after {iteration+1} iterations.")
            pi = pi_new
            break

        pi = pi_new
    else:
        logging.warning(f"Did not converge after {max_iter} iterations.")

    # Calculate final scores
    prestige_scores = H @ pi

    if metric == "eigenfactor":
        # Eigenfactor: Normalize to sum to 100
        total_score = prestige_scores.sum()
        if total_score > 0:
            scores = 100 * prestige_scores / total_score
        else:
            scores = prestige_scores
    else:
        # SJR and AIS: Normalize by article count, then scale so mean = 1.0
        scores = np.zeros(n, dtype=np.float32)
        for i, journal in enumerate(journals):
            article_count = journal_article_counts.get(journal, 0)
            if article_count > 0:
                scores[i] = prestige_scores[i] / article_count
            else:
                scores[i] = 0.0

        # Scale so that average score is 1.0
        mean_score = scores[scores > 0].mean() if np.any(scores > 0) else 1.0
        if mean_score > 0:
            scores = scores / mean_score

    return pd.DataFrame({"journal_id": journals, score_column: scores})


# Backward-compatible wrapper for tests
def calculate_eigenfactor(
    citations_df,
    journal_article_counts,
    alpha=ALPHA,
    epsilon=EPSILON,
    max_iter=MAX_ITER,
):
    """Calculate Journal Network Centrality (resembles Eigenfactor)."""
    return calculate_metric(
        citations_df,
        journal_article_counts,
        metric="eigenfactor",
        alpha=alpha,
        epsilon=epsilon,
        max_iter=max_iter,
    )


def calculate_sjr(
    citations_df,
    journal_article_counts,
    alpha=ALPHA,
    epsilon=EPSILON,
    max_iter=MAX_ITER,
    max_self_citation_ratio=MAX_SELF_CITATION_RATIO,
):
    """Calculate Prestige Weighted Rank (resembles SJR)."""
    return calculate_metric(
        citations_df,
        journal_article_counts,
        metric="sjr",
        alpha=alpha,
        epsilon=epsilon,
        max_iter=max_iter,
        max_self_citation_ratio=max_self_citation_ratio,
    )


def calculate_ais(
    citations_df,
    journal_article_counts,
    alpha=ALPHA,
    epsilon=EPSILON,
    max_iter=MAX_ITER,
):
    """Calculate Mean Article Network Score (resembles Article Influence Score)."""
    return calculate_metric(
        citations_df,
        journal_article_counts,
        metric="ais",
        alpha=alpha,
        epsilon=epsilon,
        max_iter=max_iter,
    )


def save_results(conn, df, metric="eigenfactor"):
    """
    Save the calculated scores to the database safely using Drop-and-Recreate.
    """
    table_names = {"eigenfactor": "eigenfactor", "sjr": "sjr", "ais": "ais"}
    score_columns = {
        "eigenfactor": "eigenfactor_score",
        "sjr": "sjr_score",
        "ais": "ais_score",
    }
    table_name = table_names.get(metric, "eigenfactor")
    score_column = score_columns.get(metric, "eigenfactor_score")

    logging.info(f"Saving results to rolap.{table_name}...")

    try:
        with conn:
            conn.execute(f"DROP TABLE IF EXISTS rolap.{table_name}")

            conn.execute(
                f"""
                CREATE TABLE rolap.{table_name} (
                    journal_id INTEGER PRIMARY KEY,
                    {score_column} REAL
                )
            """
            )

            insert_query = f"""
                INSERT INTO rolap.{table_name} (journal_id, {score_column}) 
                VALUES (?, ?)
            """

            data_gen = (
                (int(row[0]), float(row[1])) for row in df.itertuples(index=False)
            )

            count = 0
            while True:
                chunk = list(itertools.islice(data_gen, 10000))
                if not chunk:
                    break
                conn.executemany(insert_query, chunk)
                count += len(chunk)

        logging.info(f"Saved {count} records successfully.")

    except sqlite3.Error as e:
        logging.critical(f"Database error during save: {e}")
        raise


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate journal network centrality (prestige) metrics"
    )
    parser.add_argument(
        "--metric",
        choices=["eigenfactor", "sjr", "ais"],
        default="eigenfactor",
        help="Metric to calculate",
    )
    parser.add_argument("--db", required=True, help="Path to the main SQLite database")
    parser.add_argument(
        "--rolap-db",
        required=True,
        help="Path to the ROLAP SQLite database (can be same as main)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    metric = args.metric

    logging.info(f"Calculating {metric.upper()} metric...")

    conn = None
    try:
        conn = get_db_connection(args.db, args.rolap_db)
        citations_df, journal_article_counts = load_data(conn, metric)

        if citations_df.empty:
            logging.critical("No citation data found.")
            return

        results_df = calculate_metric(
            citations_df, journal_article_counts, metric=metric
        )
        save_results(conn, results_df, metric)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
