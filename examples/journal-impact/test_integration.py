#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2026  Panagiotis Spanakis
# SPDX-License-Identifier: GPL-3.0-or-later
#

"""Integration tests for Python-based metric scripts.

These tests replace the former calculate_*.sql + calculate_*.rdbu pairs
which used .shell/.save commands to manipulate temporary database files.
Each test creates a temporary SQLite database, populates it with fixture
data, runs the corresponding Python script via subprocess, and verifies
the results.
"""

import os
import sqlite3
import subprocess
import tempfile

import pytest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _create_test_db(tables):
    """Create a temporary SQLite database and populate it with fixture data.

    ``tables`` is a dict mapping table names to (columns, rows) tuples.
    Returns the path to the temporary database file.
    """
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(db_path)
    for table_name, (columns, rows) in tables.items():
        col_defs = ", ".join(f"{c} REAL" if c != columns[0] else f"{c} INTEGER"
                            for c in columns)
        conn.execute(f"CREATE TABLE {table_name} ({col_defs})")
        placeholders = ", ".join("?" for _ in columns)
        conn.executemany(
            f"INSERT INTO {table_name} VALUES ({placeholders})", rows
        )
    conn.commit()
    conn.close()
    return db_path


def _run_script(script_name, *extra_args, test_db=None):
    """Run a Python metric script and return the subprocess result."""
    cmd = [os.path.join(SCRIPT_DIR, script_name)]
    if test_db:
        cmd.extend(["--test-db", test_db])
    cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return result


def _read_table(db_path, table_name):
    """Read all rows from a table, returning (column_names, rows)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return columns, rows


# ── Network Centrality ──────────────────────────────────────────────


class TestNetworkCentrality:
    """Symmetric 2-journal ring: each journal gets 50% of total centrality."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        self.db_path = _create_test_db({
            "publications5": (
                ["journal_id", "publications_number"],
                [(100, 10), (200, 10)],
            ),
            "citation_network": (
                ["citing_journal", "cited_journal", "citation_count"],
                [(100, 200, 10), (200, 100, 10)],
            ),
        })
        yield
        os.unlink(self.db_path)

    def test_runs_successfully(self):
        result = _run_script(
            "journal_network_metrics.py",
            "--metric", "network_centrality",
            test_db=self.db_path,
        )
        assert result.returncode == 0, result.stderr

    def test_symmetric_centrality(self):
        _run_script(
            "journal_network_metrics.py",
            "--metric", "network_centrality",
            test_db=self.db_path,
        )
        _, rows = _read_table(self.db_path, "network_centrality")
        scores = {int(r[0]): r[1] for r in rows}
        assert scores[100] == pytest.approx(50.0, abs=0.1)
        assert scores[200] == pytest.approx(50.0, abs=0.1)


# ── Prestige Rank ───────────────────────────────────────────────────


class TestPrestigeRank:
    """Symmetric 2-journal network with self-citations: both get prestige 1.0."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        self.db_path = _create_test_db({
            "publications3": (
                ["journal_id", "publications_number"],
                [(100, 10), (200, 10)],
            ),
            "citation_network3": (
                ["citing_journal", "cited_journal", "citation_count"],
                [
                    (100, 200, 10),
                    (200, 100, 10),
                    (100, 100, 2),
                    (200, 200, 2),
                ],
            ),
        })
        yield
        os.unlink(self.db_path)

    def test_runs_successfully(self):
        result = _run_script(
            "journal_network_metrics.py",
            "--metric", "prestige_rank",
            test_db=self.db_path,
        )
        assert result.returncode == 0, result.stderr

    def test_symmetric_prestige(self):
        _run_script(
            "journal_network_metrics.py",
            "--metric", "prestige_rank",
            test_db=self.db_path,
        )
        _, rows = _read_table(self.db_path, "prestige_rank")
        scores = {int(r[0]): r[1] for r in rows}
        assert scores[100] == pytest.approx(1.0, abs=0.01)
        assert scores[200] == pytest.approx(1.0, abs=0.01)


# ── Mean Article Score ──────────────────────────────────────────────


class TestMeanArticleScore:
    """Symmetric 2-journal network: both get mean article score 1.0."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        self.db_path = _create_test_db({
            "publications5": (
                ["journal_id", "publications_number"],
                [(100, 10), (200, 10)],
            ),
            "citation_network": (
                ["citing_journal", "cited_journal", "citation_count"],
                [(100, 200, 10), (200, 100, 10)],
            ),
        })
        yield
        os.unlink(self.db_path)

    def test_runs_successfully(self):
        result = _run_script(
            "journal_network_metrics.py",
            "--metric", "mean_article_score",
            test_db=self.db_path,
        )
        assert result.returncode == 0, result.stderr

    def test_symmetric_mean_score(self):
        _run_script(
            "journal_network_metrics.py",
            "--metric", "mean_article_score",
            test_db=self.db_path,
        )
        _, rows = _read_table(self.db_path, "mean_article_score")
        scores = {int(r[0]): r[1] for r in rows}
        assert scores[100] == pytest.approx(1.0, abs=0.01)
        assert scores[200] == pytest.approx(1.0, abs=0.01)


# ── Context Normalized Impact ───────────────────────────────────────


class TestContextNormalizedImpact:
    """Symmetric 2-journal coupling: both get impact_score 0.1."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        self.db_path = _create_test_db({
            "publications3": (
                ["journal_id", "publications_number"],
                [(100, 5), (200, 5)],
            ),
            "citation_network3": (
                ["citing_journal", "cited_journal", "citation_count"],
                [(100, 200, 10), (200, 100, 10)],
            ),
            "bibliographic_coupling": (
                ["journal_a", "journal_b", "coupling_strength"],
                [(100, 200, 50)],
            ),
            "journal_reference_density": (
                ["journal_id", "avg_references"],
                [(100, 20.0), (200, 20.0)],
            ),
        })
        yield
        os.unlink(self.db_path)

    def test_runs_successfully(self):
        result = _run_script(
            "context_normalized_impact.py",
            test_db=self.db_path,
        )
        assert result.returncode == 0, result.stderr

    def test_symmetric_impact(self):
        _run_script(
            "context_normalized_impact.py",
            test_db=self.db_path,
        )
        _, rows = _read_table(self.db_path, "context_impact")
        results = {int(r[0]): {"impact_score": r[1], "raw_impact": r[2],
                                "citation_potential": r[3]} for r in rows}
        assert results[100]["impact_score"] == pytest.approx(0.1, abs=0.01)
        assert results[200]["impact_score"] == pytest.approx(0.1, abs=0.01)
        assert results[100]["raw_impact"] == pytest.approx(2.0, abs=0.01)
        assert results[200]["raw_impact"] == pytest.approx(2.0, abs=0.01)
        assert results[100]["citation_potential"] == pytest.approx(20.0, abs=0.1)
        assert results[200]["citation_potential"] == pytest.approx(20.0, abs=0.1)
