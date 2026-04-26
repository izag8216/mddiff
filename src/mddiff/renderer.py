"""Rich terminal renderer for diff output."""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from .differ import ChangeType, DiffResult, SectionDiff

THEME = Theme(
    {
        "added": "bold green",
        "deleted": "bold red",
        "modified": "bold yellow",
        "moved": "bold cyan",
        "unchanged": "dim",
        "header": "bold white on dark_green",
        "stat.added": "green",
        "stat.deleted": "red",
        "stat.modified": "yellow",
        "stat.moved": "cyan",
    }
)

CHANGE_ICONS = {
    ChangeType.ADDED: "[added]+[/added]",
    ChangeType.DELETED: "[deleted]-[/deleted]",
    ChangeType.MODIFIED: "[modified]~[/modified]",
    ChangeType.MOVED: "[moved]<->[/moved]",
    ChangeType.UNCHANGED: "[unchanged] [/unchanged]",
}


def _format_inline_line(prefix: str, line: str) -> Text:
    """Format a single inline diff line."""
    if prefix == "+":
        return Text(f"  + {line}", style="green")
    elif prefix == "-":
        return Text(f"  - {line}", style="red")
    else:
        return Text(f"    {line}", style="dim")


def render_diff(
    result: DiffResult,
    console: Optional[Console] = None,
    show_inline: bool = True,
    show_unchanged: bool = False,
    summary_only: bool = False,
    section_filter: Optional[str] = None,
) -> None:
    """Render diff result to terminal."""
    if console is None:
        console = Console(theme=THEME)

    if summary_only:
        _render_summary(result, console)
        return

    for sd in result.section_diffs:
        if section_filter and section_filter.lower() not in sd.title.lower():
            continue
        if sd.change_type == ChangeType.UNCHANGED and not show_unchanged:
            continue
        _render_section_diff(sd, console, show_inline)

    _render_summary(result, console)


def _render_section_diff(sd: SectionDiff, console: Console, show_inline: bool) -> None:
    """Render a single section diff."""
    icon = CHANGE_ICONS[sd.change_type]
    header = f"{icon} {'#' * sd.section.level} {sd.title}"

    if sd.change_type == ChangeType.UNCHANGED:
        console.print(f"  {header}", style="dim")
        return

    style_map = {
        ChangeType.ADDED: "green",
        ChangeType.DELETED: "red",
        ChangeType.MODIFIED: "yellow",
        ChangeType.MOVED: "cyan",
    }
    style = style_map.get(sd.change_type, "white")

    border_style = style
    title = f"{icon} {'#' * sd.section.level} {sd.title}"

    content_lines = []
    if sd.change_type == ChangeType.MOVED and sd.old_section:
        content_lines.append(
            Text(f"  Moved from line {sd.old_section.line_start}", style="cyan")
        )
    elif sd.change_type == ChangeType.ADDED:
        body = sd.section.body.strip()
        if body:
            for line in body.splitlines()[:20]:
                content_lines.append(Text(f"  + {line}", style="green"))
            if len(body.splitlines()) > 20:
                content_lines.append(
                    Text(f"  ... ({len(body.splitlines()) - 20} more lines)", style="dim")
                )
    elif sd.change_type == ChangeType.DELETED:
        body = sd.section.body.strip()
        if body:
            for line in body.splitlines()[:20]:
                content_lines.append(Text(f"  - {line}", style="red"))
            if len(body.splitlines()) > 20:
                content_lines.append(
                    Text(f"  ... ({len(body.splitlines()) - 20} more lines)", style="dim")
                )
    elif sd.change_type == ChangeType.MODIFIED and show_inline and sd.inline_changes:
        for prefix, line in sd.inline_changes[:40]:
            content_lines.append(_format_inline_line(prefix, line))
        if len(sd.inline_changes) > 40:
            content_lines.append(
                Text(
                    f"  ... ({len(sd.inline_changes) - 40} more changes)",
                    style="dim",
                )
            )

    panel_content = Text("\n").join(content_lines) if content_lines else Text("  (no content)", style="dim")
    panel = Panel(
        panel_content,
        title=title,
        title_align="left",
        border_style=border_style,
        padding=(0, 1),
    )
    console.print(panel)


def _render_summary(result: DiffResult, console: Console) -> None:
    """Render diff summary statistics."""
    stats = result.stats
    table = Table(
        title="Diff Summary",
        show_header=True,
        header_style="bold",
        border_style="dim",
    )
    table.add_column("Change", style="bold")
    table.add_column("Count", justify="right")

    if stats["added"]:
        table.add_row("[green]+ Added[/green]", str(stats["added"]))
    if stats["deleted"]:
        table.add_row("[red]- Deleted[/red]", str(stats["deleted"]))
    if stats["modified"]:
        table.add_row("[yellow]~ Modified[/yellow]", str(stats["modified"]))
    if stats["moved"]:
        table.add_row("[cyan]<-> Moved[/cyan]", str(stats["moved"]))
    table.add_row("[dim]  Unchanged[/dim]", str(stats["unchanged"]))
    table.add_row("[bold]  Total[/bold]", str(sum(stats.values())))

    console.print()
    console.print(table)
