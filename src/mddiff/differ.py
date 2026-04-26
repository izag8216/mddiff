"""Semantic diff engine -- compares Markdown sections."""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .parser import Section, parse_sections, section_key


class ChangeType(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    MOVED = "moved"
    UNCHANGED = "unchanged"


@dataclass
class SectionDiff:
    """Result of comparing a single section."""

    change_type: ChangeType
    section: Section
    old_section: Optional[Section] = None
    inline_changes: List[Tuple[str, str]] = field(default_factory=list)
    similarity: float = 1.0

    @property
    def title(self) -> str:
        return self.section.title


@dataclass
class DiffResult:
    """Complete diff between two Markdown documents."""

    old_sections: List[Section]
    new_sections: List[Section]
    section_diffs: List[SectionDiff]
    stats: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        self.stats = {
            "added": sum(1 for d in self.section_diffs if d.change_type == ChangeType.ADDED),
            "deleted": sum(1 for d in self.section_diffs if d.change_type == ChangeType.DELETED),
            "modified": sum(1 for d in self.section_diffs if d.change_type == ChangeType.MODIFIED),
            "moved": sum(1 for d in self.section_diffs if d.change_type == ChangeType.MOVED),
            "unchanged": sum(1 for d in self.section_diffs if d.change_type == ChangeType.UNCHANGED),
        }


def _similarity(a: str, b: str) -> float:
    """Return similarity ratio between two strings."""
    return difflib.SequenceMatcher(None, a, b).ratio()


def _compute_inline_diff(old_body: str, new_body: str) -> List[Tuple[str, str]]:
    """Compute line-level inline diff between two bodies.

    Returns list of (tag, line) where tag is '+', '-', or ' '.
    """
    old_lines = old_body.splitlines()
    new_lines = new_body.splitlines()
    result: List[Tuple[str, str]] = []

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for line in old_lines[i1:i2]:
                result.append((" ", line))
        elif tag == "replace":
            for line in old_lines[i1:i2]:
                result.append(("-", line))
            for line in new_lines[j1:j2]:
                result.append(("+", line))
        elif tag == "delete":
            for line in old_lines[i1:i2]:
                result.append(("-", line))
        elif tag == "insert":
            for line in new_lines[j1:j2]:
                result.append(("+", line))

    return result


def compute_diff(old_text: str, new_text: str) -> DiffResult:
    """Compute semantic section-level diff between two Markdown documents."""
    old_sections = parse_sections(old_text)
    new_sections = parse_sections(new_text)

    old_map: Dict[str, Section] = {section_key(s): s for s in old_sections}
    new_map: Dict[str, Section] = {section_key(s): s for s in new_sections}

    old_keys = [section_key(s) for s in old_sections]
    new_keys = [section_key(s) for s in new_sections]

    diffs: List[SectionDiff] = []
    processed_new: set = set()
    processed_old: set = set()

    # Pass 1: exact key matches
    for key in new_keys:
        if key in old_map:
            old_s = old_map[key]
            new_s = new_map[key]
            sim = _similarity(old_s.full_text, new_s.full_text)
            if sim >= 0.90:
                diffs.append(
                    SectionDiff(
                        change_type=ChangeType.UNCHANGED,
                        section=new_s,
                        old_section=old_s,
                        similarity=sim,
                    )
                )
            else:
                diffs.append(
                    SectionDiff(
                        change_type=ChangeType.MODIFIED,
                        section=new_s,
                        old_section=old_s,
                        inline_changes=_compute_inline_diff(old_s.body, new_s.body),
                        similarity=sim,
                    )
                )
            processed_new.add(key)
            processed_old.add(key)

    # Pass 2: detect moved / modified sections (same title, different position)
    for key in new_keys:
        if key in processed_new:
            continue
        new_s = new_map[key]
        # Look for best match in old sections by title similarity
        best_match: Optional[Section] = None
        best_sim = 0.0
        for old_key in old_keys:
            if old_key in processed_old:
                continue
            old_s = old_map[old_key]
            title_sim = _similarity(new_s.title.lower(), old_s.title.lower())
            body_sim = _similarity(new_s.body, old_s.body)
            combined = title_sim * 0.4 + body_sim * 0.6
            if combined > best_sim:
                best_sim = combined
                best_match = old_s

        if best_match and best_sim > 0.5:
            old_key = section_key(best_match)
            if best_sim > 0.85:
                # Same section, moved
                diffs.append(
                    SectionDiff(
                        change_type=ChangeType.MOVED,
                        section=new_s,
                        old_section=best_match,
                        similarity=best_sim,
                    )
                )
            else:
                # Modified significantly
                diffs.append(
                    SectionDiff(
                        change_type=ChangeType.MODIFIED,
                        section=new_s,
                        old_section=best_match,
                        inline_changes=_compute_inline_diff(best_match.body, new_s.body),
                        similarity=best_sim,
                    )
                )
            processed_new.add(key)
            processed_old.add(old_key)
        else:
            diffs.append(
                SectionDiff(
                    change_type=ChangeType.ADDED,
                    section=new_s,
                    similarity=0.0,
                )
            )
            processed_new.add(key)

    # Pass 3: deleted sections
    for key in old_keys:
        if key not in processed_old:
            old_s = old_map[key]
            diffs.append(
                SectionDiff(
                    change_type=ChangeType.DELETED,
                    section=old_s,
                    similarity=0.0,
                )
            )

    # Order: use new document order, then deleted at end
    ordered: List[SectionDiff] = []
    new_key_order = {key: i for i, key in enumerate(new_keys)}
    for d in diffs:
        if d.change_type == ChangeType.DELETED:
            ordered.append(d)
        else:
            key = section_key(d.section)
            ordered.append(d)

    # Sort non-deleted by position in new doc, deleted at end
    non_deleted = [d for d in diffs if d.change_type != ChangeType.DELETED]
    deleted = [d for d in diffs if d.change_type == ChangeType.DELETED]

    def sort_key(d: SectionDiff) -> int:
        k = section_key(d.section)
        return new_key_order.get(k, 9999)

    non_deleted.sort(key=sort_key)
    ordered = non_deleted + deleted

    return DiffResult(
        old_sections=old_sections,
        new_sections=new_sections,
        section_diffs=ordered,
    )
