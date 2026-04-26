"""Markdown parser -- splits documents into sections by headers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Section:
    """A single Markdown section headed by a header line."""

    level: int
    title: str
    body: str
    line_start: int
    line_end: int
    children: List["Section"] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        header = "#" * self.level + " " + self.title
        return header + "\n" + self.body if self.body else header

    @property
    def anchor(self) -> str:
        return self.title.lower().strip().replace(" ", "-")


HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$")


def parse_sections(text: str) -> List[Section]:
    """Parse markdown text into a flat list of sections.

    Each section starts at a header line. Text before the first header
    is captured as a level-0 section titled "(preamble)".
    """
    lines = text.splitlines()
    sections: List[Section] = []
    current_level = 0
    current_title = "(preamble)"
    current_lines: List[str] = []
    current_start = 1

    for i, line in enumerate(lines, start=1):
        m = HEADER_RE.match(line)
        if m:
            if current_lines or current_title != "(preamble)":
                body = "\n".join(current_lines)
                sections.append(
                    Section(
                        level=current_level,
                        title=current_title,
                        body=body,
                        line_start=current_start,
                        line_end=i - 1,
                    )
                )
            current_level = len(m.group(1))
            current_title = m.group(2).strip()
            current_lines = []
            current_start = i
        else:
            current_lines.append(line)

    # last section
    body = "\n".join(current_lines)
    sections.append(
        Section(
            level=current_level,
            title=current_title,
            body=body,
            line_start=current_start,
            line_end=len(lines),
        )
    )

    return sections


def section_key(section: Section) -> str:
    """Stable key for matching sections across documents."""
    return f"h{section.level}:{section.title.lower().strip()}"
