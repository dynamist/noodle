"""scripts/postgres-version.sh, with a stub docker standing in for the Odoo image."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "postgres-version.sh"


@pytest.fixture
def run(tmp_path):
    """Run a copy of the script in a fake repo, with Odoo 20 needing PostgreSQL 13."""
    (tmp_path / "scripts").mkdir()
    shutil.copy(SCRIPT, tmp_path / "scripts")
    (tmp_path / "k8s" / "base").mkdir(parents=True)
    (tmp_path / "bin").mkdir()
    docker = tmp_path / "bin" / "docker"
    docker.write_text("#!/bin/sh\necho 20.0 13\n")
    docker.chmod(0o755)

    def run(pg="", images=("postgres:17", "postgres:17")):
        manifest = "".join(f"        - name: c{i}\n          image: {image}\n" for i, image in enumerate(images))
        (tmp_path / "k8s" / "base" / "postgres.yaml").write_text(manifest)
        env = {**os.environ, "PATH": f"{tmp_path / 'bin'}:{os.environ['PATH']}"}
        return subprocess.run(
            [tmp_path / "scripts" / SCRIPT.name, "odoo:test", pg], env=env, capture_output=True, text=True
        )

    return run


def test_default_is_the_manifest_tag(run):
    result = run()
    assert (result.returncode, result.stdout) == (0, "17\n"), result.stderr


def test_default_refuses_different_tags(run):
    result = run(images=("postgres:17", "postgres:16"))
    assert result.returncode != 0
    assert "different postgres images" in result.stderr


def test_default_needs_a_tag(run):
    assert run(images=("postgres:latest",)).returncode != 0


def test_explicit_version(run):
    assert run("16").stdout == "16\n"


def test_min(run):
    assert run("min").stdout == "13\n"


@pytest.mark.parametrize("pg", ["12", "17.2", "latest"])
def test_refuses(run, pg):
    result = run(pg)
    assert (result.returncode, result.stdout) == (1, "")
