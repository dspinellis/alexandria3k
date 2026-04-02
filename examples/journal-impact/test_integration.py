"""Integration tests for journal-impact metric calculation scripts.

Each test class populates a temporary SQLite database with fixture data,
invokes the corresponding Python script via subprocess, and verifies
that the expected result table is produced.

These tests replace the former calculate_*.{sql,rdbu} rdbunit wrappers,
providing the same coverage through pytest.
"""

import os
import sqlite3
import subprocess
import sys
import tempfile

import pytest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _run_script(script, args, cwd=SCRIPT_DIR):
    """Run a Python script as a subprocess and assert success."""
    result = subprocess.run(
        [sys.executable, os.path.join(cwd, script), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"{script} failed (rc={result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    return result


class TestNetworkCentrality:
    """Mirrors calculate_network_centrality.rdbu."""

    def test_symmetric_network(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("ATTACH DATABASE ? AS rolap", (db_path,))

        # Fixture: publications5
        conn.execute(
            "CREATE TABLE publications5 "
            "(journal_id INTEGER, publications_number INTEGER)"
        )
        conn.executemany(
            "INSERT INTO publications5 VALUES (?, ?)",
            [(100, 10), (200, 10)],
        )

        # Fixture: citation_network
        conn.execute(
            "CREATE TABLE citation_network "
            "(citing_journal INTEGER, cited_journal INTEGER, "
            "citation_count INTEGER)"
        )
        conn.executemany(
            "INSERT INTO citation_network VALUES (?, ?, ?)",
            [(100, 200, 10), (200, 100, 10)],
        )
        conn.commit()
        conn.close()

        _run_script(
            "journal_network_metrics.py",
            ["--metric", "network_centrality", "--db", db_path,
             "--rolap-db", db_path],
        )

        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT journal_id, centrality_score FROM network_centrality "
            "ORDER BY journal_id"
        ).fetchall()
        conn.close()

        assert len(rows) == 2
        assert rows[0] == (100, 50.0)
        assert rows[1] == (200, 50.0)


class TestPrestigeRank:
    """Mirrors calculate_prestige_rank.rdbu."""

    def test_symmetric_with_self_citations(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("ATTACH DATABASE ? AS rolap", (db_path,))

        conn.execute(
            "CREATE TABLE publications3 "
            "(journal_id INTEGER, publications_number INTEGER)"
        )
        conn.executemany(
            "INSERT INTO publications3 VALUES (?, ?)",
            [(100, 10), (200, 10)],
        )

        conn.execute(
            "CREATE TABLE citation_network3 "
            "(citing_journal INTEGER, cited_journal INTEGER, "
            "citation_count INTEGER)"
        )
        conn.executemany(
            "INSERT INTO citation_network3 VALUES (?, ?, ?)",
            [
                (100, 200, 10),
                (200, 100, 10),
                (100, 100, 2),
                (200, 200, 2),
            ],
        )
        conn.commit()
        conn.close()

        _run_script(
            "journal_network_metrics.py",
            ["--metric", "prestige_rank", "--db", db_path,
             "--rolap-db", db_path],
        )

        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT journal_id, prestige_score FROM prestige_rank "
            "ORDER BY journal_id"
        ).fetchall()
        conn.close()

        assert len(rows) == 2
        assert rows[0] == (100, 1.0)
        assert rows[1] == (200, 1.0)


class TestMeanArticleScore:
    """Mirrors calculate_mean_article_score.rdbu."""

    def test_symmetric_mean_score(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("ATTACH DATABASE ? AS rolap", (db_path,))

        conn.execute(
            "CREATE TABLE publications5 "
            "(journal_id INTEGER, publications_number INTEGER)"
        )
        conn.executemany(
            "INSERT INTO publications5 VALUES (?, ?)",
            [(100, 10), (200, 10)],
        )

        conn.execute(
            "CREATE TABLE citation_network "
            "(citing_journal INTEGER, cited_journal INTEGER, "
            "citation_count INTEGER)"
        )
        conn.executemany(
            "INSERT INTO citation_network VALUES (?, ?, ?)",
            [(100, 200, 10), (200, 100, 10)],
        )
        conn.commit()
        conn.close()

        _run_script(
            "journal_network_metrics.py",
            ["--metric", "mean_article_score", "--db", db_path,
             "--rolap-db", db_path],
        )

        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT journal_id, mean_score FROM mean_article_score "
            "ORDER BY journal_id"
        ).fetchall()
        conn.close()

        assert len(rows) == 2
        assert rows[0] == (100, 1.0)
        assert rows[1] == (200, 1.0)


class TestContextNormalizedImpact:
    """Mirrors calculate_context_impact.rdbu."""

    def test_symmetric_context_impact(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("ATTACH DATABASE ? AS rolap", (db_path,))

        # publications3
        conn.execute(
            "CREATE TABLE publications3 "
            "(journal_id INTEGER, publications_number INTEGER)"
        )
        conn.executemany(
            "INSERT INTO publications3 VALUES (?, ?)",
            [(100, 5), (200, 5)],
        )

        # citation_network3
        conn.execute(
            "CREATE TABLE citation_network3 "
            "(citing_journal INTEGER, cited_journal INTEGER, "
            "citation_count INTEGER)"
        )
        conn.executemany(
            "INSERT INTO citation_network3 VALUES (?, ?, ?)",
            [(100, 200, 10), (200, 100, 10)],
        )

        # bibliographic_coupling
        conn.execute(
            "CREATE TABLE bibliographic_coupling "
            "(journal_a INTEGER, journal_b INTEGER, "
            "coupling_strength REAL)"
        )
        conn.execute(
            "INSERT INTO bibliographic_coupling VALUES (?, ?, ?)",
            (100, 200, 50),
        )

        # journal_reference_density
        conn.execute(
            "CREATE TABLE journal_reference_density "
            "(journal_id INTEGER, avg_references REAL)"
        )
        conn.executemany(
            "INSERT INTO journal_reference_density VALUES (?, ?)",
            [(100, 20.0), (200, 20.0)],
        )
        conn.commit()
        conn.close()

        _run_script(
            "context_normalized_impact.py",
            ["--db", db_path, "--rolap-db", db_path],
        )

        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT journal_id, impact_score, raw_impact, "
            "citation_potential FROM context_impact ORDER BY journal_id"
        ).fetchall()
        conn.close()

        assert len(rows) == 2
        # Both journals symmetric: impact_score = raw_impact / potential
        # raw_impact = citations/papers = 10/5 = 2.0
        # citation_potential = 20.0 (avg_references)
        # impact_score = 2.0/20.0 = 0.1
        for row in rows:
            assert row[1] == pytest.approx(0.1, abs=0.01)
            assert row[2] == pytest.approx(2.0, abs=0.01)
            assert row[3] == pytest.approx(20.0, abs=0.01)
