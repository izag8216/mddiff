"""Tests for mddiff differ."""

from src.mddiff.differ import ChangeType, compute_diff


class TestComputeDiff:
    def test_identical_documents(self):
        text = "# Hello\n\nSame content."
        result = compute_diff(text, text)
        assert result.stats["unchanged"] == 1
        assert result.stats["added"] == 0
        assert result.stats["deleted"] == 0

    def test_added_section(self):
        old = "# Intro\n\nHello"
        new = "# Intro\n\nHello\n\n## New\n\nNew content"
        result = compute_diff(old, new)
        assert result.stats["added"] == 1
        assert result.stats["unchanged"] == 1

    def test_deleted_section(self):
        old = "# Intro\n\nHello\n\n## Removed\n\nGone"
        new = "# Intro\n\nHello"
        result = compute_diff(old, new)
        assert result.stats["deleted"] == 1

    def test_modified_section(self):
        old = "# Intro\n\nOld content"
        new = "# Intro\n\nNew content with lots of changes here"
        result = compute_diff(old, new)
        modified = [d for d in result.section_diffs if d.change_type == ChangeType.MODIFIED]
        assert len(modified) == 1
        assert len(modified[0].inline_changes) > 0

    def test_reordered_sections_unchanged(self):
        old = "# A\n\nAlpha\n\n# B\n\nBeta\n\n# C\n\nCharlie"
        new = "# A\n\nAlpha\n\n# C\n\nCharlie\n\n# B\n\nBeta"
        result = compute_diff(old, new)
        # Identical sections reordered = all unchanged (no preamble since starts with header)
        assert result.stats["unchanged"] == 3
        assert result.stats["added"] == 0
        assert result.stats["deleted"] == 0

    def test_moved_section_with_rename(self):
        old = "# Intro\n\nHello\n\n# Getting Started\n\nSetup guide"
        new = "# Introduction\n\nHello\n\n# Quick Start\n\nSetup guide"
        result = compute_diff(old, new)
        # Sections with different titles but similar content = modified or moved
        changed = [d for d in result.section_diffs if d.change_type != ChangeType.UNCHANGED]
        assert len(changed) >= 1

    def test_inline_diff_generation(self):
        old = "# Test\n\nLine 1\nLine 2\nLine 3"
        new = "# Test\n\nLine 1\nLine CHANGED\nLine 3"
        result = compute_diff(old, new)
        modified = [d for d in result.section_diffs if d.change_type == ChangeType.MODIFIED]
        assert len(modified) == 1
        changes = modified[0].inline_changes
        assert any(c[0] == "-" for c in changes)
        assert any(c[0] == "+" for c in changes)

    def test_stats_correctness(self):
        old = "# A\n\nAlpha\n\n# B\n\nBeta"
        new = "# A\n\nAlpha changed\n\n# C\n\nCharlie"
        result = compute_diff(old, new)
        total = sum(result.stats.values())
        assert total == len(result.section_diffs)
