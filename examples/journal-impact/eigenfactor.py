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
Calculate Eigenfactor scores for journals in the Alexandria3k database.

This script calculates the Eigenfactor score for each journal based on the
citation network in a specific year (reference year) to articles published
in the preceding 5 years.

It connects to the SQLite databases `rolap.db` and the main database (defined
by MAINDB environment variable), reads the citation network and article counts,
computes the Eigenfactor scores using the power iteration method on the
sparse adjacency matrix, and saves the results to `rolap.eigenfactor`.

The calculation follows the standard Eigenfactor algorithm:
1. Construct the citation matrix H (citations from citing journal to cited journal).
2. Normalize columns of H (column-stochastic).
3. Handle dangling nodes (journals that don't cite others) by distributing their
   influence according to the article vector.
4. Apply the teleportation parameter (alpha = 0.85).
5. Compute the principal eigenvector using power iteration.
6. Calculate Eigenfactor score = H * pi (influence received).

Environment Variables:
    MAINDB: Path to the main database (without .db extension). Default: 'impact'
    ROLAPDB: Path to the ROLAP database (without .db extension). Default: 'rolap'
"""

import os
import sys
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


def get_db_connection():
    """
    Establish connection to the main database and attach the ROLAP database.
    """
    main_db_path = os.environ.get("MAINDB", "impact")
    rolap_db_path = os.environ.get("ROLAPDB", "rolap")

    # Ensure paths are absolute or correctly relative
    # If they are just filenames, they are relative to CWD.

    db_file = f"{main_db_path}.db"
    if not os.path.exists(db_file):
        # Try looking in /tmp/impact.db if default
        if main_db_path == "impact" and os.path.exists("/tmp/impact.db"):
            db_file = "/tmp/impact.db"
        elif not os.path.exists(db_file):
            logging.warning(f"Main database file '{db_file}' not found.")

    logging.info(f"Connecting to {db_file}...")
    conn = sqlite3.connect(db_file)

    rolap_file = f"{rolap_db_path}.db"
    logging.info(f"Attaching {rolap_file} as rolap...")
    conn.execute(f"ATTACH DATABASE '{rolap_file}' AS rolap")

    return conn


def load_data(conn):
    """
    Load citation network and article counts from the database.

    This function retrieves the pre-calculated data needed for the Eigenfactor algorithm:
    1. Article Counts (Article Vector): The number of citable works for each journal
       in the 5-year window. This is used to distribute the influence of dangling nodes.
       It reads from the `rolap.article_counts` table.

    2. Citation Network (Adjacency Matrix): The aggregated citation counts between journals.
       It reads from the `rolap.citation_network` table.

    Returns:
        tuple: (citations_df, journal_article_counts)
    """
    # 1. Get Article Counts (Article Vector)
    # Use the pre-calculated publications5 table if available, otherwise calculate.
    logging.info("Fetching article counts...")

    article_query = """
        SELECT journal_id, publications_number AS article_count
        FROM rolap.publications5
    """
    articles_df = pd.read_sql_query(article_query, conn)

    journal_article_counts = dict(
        zip(articles_df["journal_id"], articles_df["article_count"])
    )
    logging.info(f"Found {len(journal_article_counts)} journals with citable works.")

    # 2. Get Citation Network
    # Use the pre-calculated citation_network table.
    logging.info("Fetching citation network...")
    citation_query = """
        SELECT
          citing_journal,
          cited_journal,
          citation_count
        FROM rolap.citation_network
    """
    try:
        citations_df = pd.read_sql_query(citation_query, conn)
        logging.info(f"Found {len(citations_df)} citation links.")
    except Exception as e:
        logging.error(f"Error reading rolap.citation_network: {e}")
        logging.error(
            "Please run 'eigenfactor.sql' to create the citation network table."
        )
        sys.exit(1)

    return citations_df, journal_article_counts


def calculate_eigenfactor(
    citations_df,
    journal_article_counts,
    alpha=ALPHA,
    epsilon=EPSILON,
    max_iter=MAX_ITER,
):
    """
    Calculate Eigenfactor scores using sparse matrices.

    The algorithm proceeds in several steps:
    1.  **Matrix Construction**: Builds a sparse adjacency matrix (Z) from the citation dataframe.
        Z[i, j] represents citations from journal i to journal j.
        Self-citations (diagonal elements) are removed.

    2.  **Column Normalization**: Transposes Z to get H (citations from j to i) and normalizes
        the columns to make the matrix column-stochastic (sum of each column = 1).

    3.  **Article Vector**: Creates a normalized vector of article counts. This vector is used
        to redistribute the probability mass from "dangling nodes" (journals that are cited
        but do not cite any other journals in the network).

    4.  **Power Iteration**: Iteratively computes the principal eigenvector (pi) of the
        modified Google Matrix. The update rule includes:
        - The flow through the citation network (alpha * H * pi)
        - The teleportation term (random jumps)
        - The redistribution of dangling node mass

    5.  **Score Calculation**: The final Eigenfactor score is defined as 100 * (H * pi).
        This represents the percentage of time a random walker spends in a journal,
        following the citation links.

    Args:
        citations_df (pd.DataFrame): DataFrame containing 'citing_journal', 'cited_journal', 'citation_count'.
        journal_article_counts (dict): Dictionary mapping journal_id to article count.
        alpha (float): Damping factor (default 0.85).
        epsilon (float): Convergence threshold.
        max_iter (int): Maximum number of iterations.

    Returns:
        pd.DataFrame: DataFrame with 'journal_id' and 'eigenfactor_score'.
    """
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
        return pd.DataFrame(columns=["journal_id", "eigenfactor_score"])

    print(f"Constructing sparse matrix for {n} journals...")

    # Map journal IDs to matrix indices
    citing_indices = citations_df["citing_journal"].map(journal_to_idx).values
    cited_indices = citations_df["cited_journal"].map(journal_to_idx).values
    counts = citations_df["citation_count"].values

    # Create sparse matrix Z (citations FROM citing TO cited)
    # Z[i, j] = citations from journal i to journal j
    Z_coo = csr_matrix(
        (counts, (citing_indices, cited_indices)), shape=(n, n), dtype=np.float32
    )

    # Remove self-citations (diagonal)
    Z_coo.setdiag(0)
    Z_coo.eliminate_zeros()

    # Transpose to get H (citations FROM j TO i) for column-stochastic formulation
    # H[i, j] is proportional to probability of moving from j to i
    H = Z_coo.T.tocsr()

    # Create Article Vector (a)
    # Normalized vector of article counts
    article_counts_arr = np.array(
        [journal_article_counts.get(j, 0) for j in journals], dtype=np.float32
    )
    total_articles = article_counts_arr.sum()

    if total_articles > 0:
        article_vector = article_counts_arr / total_articles
    else:
        print("Warning: Total article count is 0. Using uniform distribution.")
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
    print("Starting power iteration...")
    pi = np.ones(n, dtype=np.float32) / n

    for iteration in range(max_iter):
        # Calculate influence from dangling nodes
        # Dangling nodes distribute their weight according to the article vector
        dangling_sum = pi[dangling_mask].sum() if np.any(dangling_mask) else 0.0

        # H @ pi: flow through links
        pi_new = alpha * (H @ pi)

        # Teleportation + Dangling nodes
        # (alpha * dangling_sum + (1 - alpha)) * article_vector
        teleport_factor = alpha * dangling_sum + (1 - alpha)
        pi_new += teleport_factor * article_vector

        # Check convergence (L1 norm)
        diff = np.linalg.norm(pi_new - pi, ord=1)
        if diff < epsilon:
            print(f"Converged after {iteration+1} iterations.")
            pi = pi_new
            break

        pi = pi_new
    else:
        print(f"Warning: Did not converge after {max_iter} iterations.")

    # Calculate final Eigenfactor Scores
    # Eigenfactor = 100 * (H * pi) / sum(H * pi)
    # Note: The standard definition is often just 100 * (H * pi) if pi is the steady state of the modified chain.
    # But strictly, Eigenfactor is the percentage of time spent in a journal in the citation network,
    # excluding the teleportation steps?
    # Actually, Eigenfactor.org says: "The Eigenfactor score ... is 100 * (H * pi)".
    # Where pi is the leading eigenvector of the matrix P = alpha * H + (1-alpha) * a * e^T + alpha * a * d^T

    # Let's compute H @ pi
    ef_scores = H @ pi

    # Normalize to sum to 100
    total_score = ef_scores.sum()
    if total_score > 0:
        ef_scores = 100 * ef_scores / total_score

    return pd.DataFrame({"journal_id": journals, "eigenfactor_score": ef_scores})


def save_results(conn, df):
    """
    Save the calculated scores to the database.
    """
    print("Saving results to rolap.eigenfactor...")

    # Create table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS rolap.eigenfactor (
            journal_id INTEGER PRIMARY KEY,
            eigenfactor_score REAL
        )
    """
    )

    # Clear existing data
    conn.execute("DELETE FROM rolap.eigenfactor")

    # Insert new data
    # Use chunksize to avoid "too many SQL variables" or memory issues
    df.to_sql(
        "eigenfactor",
        conn,
        schema="rolap",
        if_exists="append",
        index=False,
        chunksize=1000,
    )
    conn.commit()
    print(f"Saved {len(df)} records.")


def main():
    conn = None
    try:
        conn = get_db_connection()
        citations_df, journal_article_counts = load_data(conn)

        if citations_df.empty:
            print("No citation data found. Exiting.")
            return

        results_df = calculate_eigenfactor(citations_df, journal_article_counts)
        save_results(conn, results_df)

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
