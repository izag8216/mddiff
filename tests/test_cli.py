"""Tests for mddiff CLI."""

import subprocess
import sys
from pathlib import Path

import pytest


class TestCLI:
    def test_version(self, tmp_path):
        result = subprocess.run(
            [sys.executable, "-m", "src.mddiff.cli", "--version"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert "0.1.0" in result.stdout

    def test_diff_basic(self, tmp_path):
        old = tmp_path / "old.md"
        new = tmp_path / "new.md"
        old.write_text("# Hello\n\nOld content")
        new.write_text("# Hello\n\nNew content")
        result = subprocess.run(
            [sys.executable, "-m", "src.mddiff.cli", str(old), str(new)],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0

    def test_diff_summary(self, tmp_path):
        old = tmp_path / "old.md"
        new = tmp_path / "new.md"
        old.write_text("# Hello\n\nOld")
        new.write_text("# Hello\n\nNew\n\n## Extra\n\nAdded")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.mddiff.cli",
                str(old),
                str(new),
                "--summary",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        assert "Diff Summary" in result.stdout

    def test_file_not_found(self):
        result = subprocess.run(
            [sys.executable, "-m", "src.mddiff.cli", "diff", "nonexistent.md", "also.md"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode != 0
