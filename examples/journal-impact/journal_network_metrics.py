#!/usr/bin/env python3
#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2026  Panagiotis Spanakis
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
"""examples/journal-impact journal network metrics.

This script calculates three eigenvector-centrality-based journal metrics:

- **Journal Network Centrality** (generic): total influence over a 5-year citation window,
  excluding self-citations. Resembles the Eigenfactor score.
- **Prestige Weighted Rank** (generic): prestige per article over a 3-year citation window,
  with self-citations capped at 33%. Resembles the SCImago Journal Rank (SJR) metric.
- **Mean Article Network Score** (generic): influence per article over a 5-year citation window,
  excluding self-citations. Resembles the Article Influence Score (AIS) metric.

Note on naming: the above third‑party metric names are referenced only for comparison.
They may be trademarks or registered trademarks of their respective owners.

Usage:
    ./journal_network_metrics.py
    ./journal_network_metrics.py --metric network_centrality
    ./journal_network_metrics.py --metric prestige_rank
    ./journal_network_metrics.py --metric mean_article_score

Environment Variables:
    MAINDB: Path to the main database (without .db extension). Default: 'impact'
    ROLAPDB: Path to the ROLAP database (without .db extension). Default: 'rolap'
"""

import argparse
import itertools
import logging
import os
import sqlite3

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, diags


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


ALPHA = 0.85
EPSILON = 1e-6
MAX_ITER = 1000
MAX_SELF_CITATION_RATIO = 0.33


_METRIC_ALIASES = {
    # Preferred generic metric names
    "network_centrality": "network_centrality",
    "prestige_rank": "prestige_rank",
    "mean_article_score": "mean_article_score",
    # Backward-compatibility aliases (not advertised)
    "eigenfactor": "network_centrality",
    "sjr": "prestige_rank",
    "ais": "mean_article_score",
}


def normalize_metric(metric: str) -> str:
    """Normalize metric name to the generic internal identifier."""
    if metric is None:
        return "network_centrality"
    normalized = _METRIC_ALIASES.get(str(metric).strip().lower())
    if not normalized:
        raise ValueError(
            "Unknown metric: "
            f"{metric!r}. Use one of: network_centrality, prestige_rank, mean_article_score"
        )
    return normalized


def get_db_connection(db_path: str, rolap_db_path: str) -> sqlite3.Connection:
    """Connect to the main database and attach the ROLAP database as schema 'rolap'."""
    if not os.path.exists(db_path):
        logging.critical("Main database file '%s' not found.", db_path)
        raise FileNotFoundError(f"Database file '{db_path}' not found.")

    logging.info("Connecting to %s...", db_path)
    conn = sqlite3.connect(db_path)

    if not os.path.exists(rolap_db_path):
        logging.critical("ROLAP database file '%s' not found.", rolap_db_path)
        raise FileNotFoundError(f"Database file '{rolap_db_path}' not found.")

    logging.info("Attaching %s as rolap...", rolap_db_path)
    conn.execute(f"ATTACH DATABASE '{rolap_db_path}' AS rolap")
    return conn


def load_data(conn: sqlite3.Connection, metric: str):
    """Load citation network and article counts from the database."""
    metric = normalize_metric(metric)

    if metric == "prestige_rank":
        publications_table = "publications3"
        citation_table = "citation_network3"
        window_years = 3
    else:
        publications_table = "publications5"
        citation_table = "citation_network"
        window_years = 5

    logging.info("Fetching article counts (%d-year window)...", window_years)

    article_query = f"""
        SELECT journal_id, publications_number AS article_count
        FROM rolap.{publications_table}
    """
    articles_df = pd.read_sql_query(article_query, conn)

    journal_article_counts = dict(zip(articles_df["journal_id"], articles_df["article_count"]))
    logging.info("Found %d journals with citable works.", len(journal_article_counts))

    logging.info("Fetching citation network (%d-year window)...", window_years)
    citation_query = f"""
        SELECT
          citing_journal,
          cited_journal,
          citation_count
        FROM rolap.{citation_table}
    """
    citations_df = pd.read_sql_query(citation_query, conn)
    logging.info("Found %d citation links.", len(citations_df))

    return citations_df, journal_article_counts


def calculate_metric(
    citations_df: pd.DataFrame,
    journal_article_counts: dict,
    metric: str = "network_centrality",
    alpha: float = ALPHA,
    epsilon: float = EPSILON,
    max_iter: int = MAX_ITER,
    max_self_citation_ratio: float = MAX_SELF_CITATION_RATIO,
) -> pd.DataFrame:
    """Calculate a journal network metric using sparse eigenvector centrality."""

    metric = normalize_metric(metric)

    score_columns = {
        "network_centrality": "centrality_score",
        "prestige_rank": "prestige_score",
        "mean_article_score": "mean_score",
    }
    score_column = score_columns[metric]

    journals = sorted(
        list(set(citations_df["citing_journal"]).union(set(citations_df["cited_journal"])) )
    )
    journal_to_idx = {journal: i for i, journal in enumerate(journals)}
    n = len(journals)

    if n == 0:
        return pd.DataFrame(columns=["journal_id", score_column])

    logging.info("Constructing sparse matrix for %d journals...", n)

    citing_indices = citations_df["citing_journal"].map(journal_to_idx).values
    cited_indices = citations_df["cited_journal"].map(journal_to_idx).values
    counts = citations_df["citation_count"].values.astype(np.float32)

    Z = csr_matrix((counts, (citing_indices, cited_indices)), shape=(n, n), dtype=np.float32)
    H = Z.T.tocsr()

    if metric in ("network_centrality", "mean_article_score"):
        H.setdiag(0)
        H.eliminate_zeros()
    else:
        logging.info("Capping self-citations at %.0f%% of incoming citations...", 100 * max_self_citation_ratio)
        H_lil = H.tolil()
        for j in range(n):
            col_sum = H[:, j].sum()
            if col_sum > 0:
                self_citation = H_lil[j, j]
                max_allowed = col_sum * max_self_citation_ratio
                if self_citation > max_allowed:
                    H_lil[j, j] = max_allowed
        H = H_lil.tocsr()

    article_counts_arr = np.array([journal_article_counts.get(j, 0) for j in journals], dtype=np.float32)
    total_articles = article_counts_arr.sum()

    if total_articles > 0:
        article_vector = article_counts_arr / total_articles
    else:
        logging.warning("Total article count is 0. Using uniform distribution.")
        article_vector = np.ones(n, dtype=np.float32) / n

    column_sums = np.array(H.sum(axis=0)).flatten()
    dangling_mask = column_sums == 0
    non_zero_mask = column_sums > 0

    if np.any(non_zero_mask):
        inv_col_sums = np.zeros(n, dtype=np.float32)
        inv_col_sums[non_zero_mask] = 1.0 / column_sums[non_zero_mask]
        D_inv = diags(inv_col_sums, format="csr")
        H = H @ D_inv

    logging.info("Starting power iteration...")
    pi = np.ones(n, dtype=np.float32) / n

    for iteration in range(max_iter):
        dangling_sum = pi[dangling_mask].sum() if np.any(dangling_mask) else 0.0

        pi_new = alpha * (H @ pi)

        teleport_factor = alpha * dangling_sum + (1 - alpha)
        pi_new += teleport_factor * article_vector

        diff = np.linalg.norm(pi_new - pi, ord=1)
        if diff < epsilon:
            logging.info("Converged after %d iterations.", iteration + 1)
            pi = pi_new
            break

        pi = pi_new
    else:
        logging.warning("Did not converge after %d iterations.", max_iter)

    prestige_scores = H @ pi

    if metric == "network_centrality":
        total_score = prestige_scores.sum()
        scores = 100 * prestige_scores / total_score if total_score > 0 else prestige_scores
    else:
        scores = np.zeros(n, dtype=np.float32)
        for i, journal in enumerate(journals):
            article_count = journal_article_counts.get(journal, 0)
            scores[i] = prestige_scores[i] / article_count if article_count > 0 else 0.0

        mean_score = scores[scores > 0].mean() if np.any(scores > 0) else 1.0
        if mean_score > 0:
            scores = scores / mean_score

    return pd.DataFrame({"journal_id": journals, score_column: scores})


def calculate_network_centrality(
    citations_df: pd.DataFrame,
    journal_article_counts: dict,
    alpha: float = ALPHA,
    epsilon: float = EPSILON,
    max_iter: int = MAX_ITER,
) -> pd.DataFrame:
    """Calculate Journal Network Centrality (resembles the Eigenfactor score)."""
    return calculate_metric(
        citations_df,
        journal_article_counts,
        metric="network_centrality",
        alpha=alpha,
        epsilon=epsilon,
        max_iter=max_iter,
    )


def calculate_prestige_rank(
    citations_df: pd.DataFrame,
    journal_article_counts: dict,
    alpha: float = ALPHA,
    epsilon: float = EPSILON,
    max_iter: int = MAX_ITER,
    max_self_citation_ratio: float = MAX_SELF_CITATION_RATIO,
) -> pd.DataFrame:
    """Calculate Prestige Weighted Rank (resembles the SCImago Journal Rank metric)."""
    return calculate_metric(
        citations_df,
        journal_article_counts,
        metric="prestige_rank",
        alpha=alpha,
        epsilon=epsilon,
        max_iter=max_iter,
        max_self_citation_ratio=max_self_citation_ratio,
    )


def calculate_mean_article_score(
    citations_df: pd.DataFrame,
    journal_article_counts: dict,
    alpha: float = ALPHA,
    epsilon: float = EPSILON,
    max_iter: int = MAX_ITER,
) -> pd.DataFrame:
    """Calculate Mean Article Network Score (resembles the Article Influence Score metric)."""
    return calculate_metric(
        citations_df,
        journal_article_counts,
        metric="mean_article_score",
        alpha=alpha,
        epsilon=epsilon,
        max_iter=max_iter,
    )


def save_results(conn: sqlite3.Connection, df: pd.DataFrame, metric: str) -> None:
    """Save calculated scores to the ROLAP database under generic table/column names."""

    metric = normalize_metric(metric)

    table_names = {
        "network_centrality": "network_centrality",
        "prestige_rank": "prestige_rank",
        "mean_article_score": "mean_article_score",
    }
    score_columns = {
        "network_centrality": "centrality_score",
        "prestige_rank": "prestige_score",
        "mean_article_score": "mean_score",
    }

    table_name = table_names[metric]
    score_column = score_columns[metric]

    logging.info("Saving results to rolap.%s...", table_name)

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

            insert_query = f"INSERT INTO rolap.{table_name} (journal_id, {score_column}) VALUES (?, ?)"

            data_gen = ((int(row[0]), float(row[1])) for row in df.itertuples(index=False))

            count = 0
            while True:
                chunk = list(itertools.islice(data_gen, 10000))
                if not chunk:
                    break
                conn.executemany(insert_query, chunk)
                count += len(chunk)

        logging.info("Saved %d records successfully.", count)

    except sqlite3.Error as exc:
        logging.critical("Database error during save: %s", exc)
        raise


def parse_args():
    parser = argparse.ArgumentParser(
        description="Calculate journal network metrics (generic names; see README for comparisons)"
    )
    parser.add_argument(
        "--metric",
        default="network_centrality",
        help="Metric to calculate: network_centrality, prestige_rank, mean_article_score",
    )
    parser.add_argument("--db", required=True, help="Path to the main SQLite database")
    parser.add_argument(
        "--rolap-db",
        required=True,
        help="Path to the ROLAP SQLite database (can be same as main)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metric = normalize_metric(args.metric)

    logging.info("Calculating %s...", metric)

    conn = None
    try:
        conn = get_db_connection(args.db, args.rolap_db)
        citations_df, journal_article_counts = load_data(conn, metric)

        if citations_df.empty:
            logging.critical("No citation data found.")
            return

        results_df = calculate_metric(citations_df, journal_article_counts, metric=metric)
        save_results(conn, results_df, metric)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
