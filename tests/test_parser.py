"""Tests for mddiff parser."""

from src.mddiff.parser import Section, parse_sections, section_key


class TestParseSections:
    def test_single_section(self):
        text = "# Hello\n\nSome content."
        sections = parse_sections(text)
        assert len(sections) == 1
        assert sections[0].level == 1
        assert sections[0].title == "Hello"
        assert "Some content." in sections[0].body

    def test_multiple_sections(self):
        text = "# Intro\n\nHello world\n\n## Install\n\npip install\n\n## Usage\n\nRun it"
        sections = parse_sections(text)
        assert len(sections) == 3
        assert sections[0].title == "Intro"
        assert sections[1].title == "Install"
        assert sections[2].title == "Usage"

    def test_preamble(self):
        text = "Some text before any header\n\n# First\n\nContent"
        sections = parse_sections(text)
        assert len(sections) == 2
        assert sections[0].title == "(preamble)"
        assert sections[1].title == "First"

    def test_nested_headers(self):
        text = "# H1\n\n## H2\n\n### H3\n\nBack to ## H2b"
        sections = parse_sections(text)
        titles = [s.title for s in sections]
        assert "H1" in titles
        assert "H2" in titles
        assert "H3" in titles

    def test_empty_document(self):
        text = ""
        sections = parse_sections(text)
        assert len(sections) == 1
        assert sections[0].title == "(preamble)"

    def test_section_key(self):
        s = Section(level=2, title="Install", body="", line_start=1, line_end=5)
        assert section_key(s) == "h2:install"

    def test_full_text(self):
        s = Section(level=2, title="Test", body="line1\nline2", line_start=1, line_end=3)
        assert s.full_text == "## Test\nline1\nline2"
