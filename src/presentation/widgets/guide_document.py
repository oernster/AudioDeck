"""The Guide's structure, read out of DOCUMENTATION.md and drawn as rich text.

DOCUMENTATION.md stays the one home of the guide's words: GitHub renders it,
every build stages it and the README links to it. Handed to Qt's markdown view
it read as a page of prose with each picture above its sentence, which is not
how the guides in PigeonPost and ClearBudget read. So the same file is read
here into sections of named pictures, rules, paragraphs and command blocks;
those are drawn with each picture in a column beside its name.

Only the markdown the guide uses is understood: the title, section headings,
picture entries, bullet lists, fenced blocks and paragraphs carrying bold or
code spans. Nothing is left out; a test compares every word of the file with
every word of the page.

Qt-free, so the parse and the markup sit under the coverage gate. The dialog
that shows the result lives with the other Help dialogs.

Author: Oliver Ernster
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from itertools import groupby
from typing import Iterable, Iterator

_TITLE_PREFIX = "# "
_SECTION_PREFIX = "## "
_FENCE = "```"
_BULLET = "- "

# A picture line as the guide writes one: no alt text and a path relative to
# the repository root, which Qt resolves against the bundle root.
_PICTURE = re.compile(r"^!\[\]\((?P<path>[^)]+)\)$")

# The bold lead that names an entry or a rule: "**Switch.** Applies ...".
_LEAD = re.compile(r"^\*\*(?P<name>.+?)\*\*\s*(?P<text>.*)$")

_BOLD = re.compile(r"\*\*(.+?)\*\*")

# A capturing group, so re.split keeps each code span at an odd position.
_CODE_SPAN = re.compile(r"`([^`]+)`")

# Space round a picture and its sentence, so one 48px picture never touches
# the next. The column itself is as wide as its widest picture.
_ENTRY_CELL_PADDING_PX = 6

# Space inside a command block, so its text does not sit on the tinted edge.
_CODE_CELL_PADDING_PX = 8


@dataclass(frozen=True, slots=True)
class GuideEntry:
    """A named picture: the artwork it draws, its bold name, what it does."""

    pictures: tuple[str, ...]
    name: str
    text: str


@dataclass(frozen=True, slots=True)
class GuideRule:
    """A bullet item: a claim in bold, then what it means in practice."""

    name: str
    text: str


@dataclass(frozen=True, slots=True)
class GuideParagraph:
    """Plain prose, its source lines joined into one."""

    text: str


@dataclass(frozen=True, slots=True)
class GuideCode:
    """A fenced block, kept line for line."""

    text: str


GuideBlock = GuideEntry | GuideRule | GuideParagraph | GuideCode


@dataclass(frozen=True, slots=True)
class GuideSection:
    """One heading and the blocks under it; the opening section has none."""

    heading: str
    blocks: tuple[GuideBlock, ...]


@dataclass(frozen=True, slots=True)
class GuideDocument:
    """The whole guide: its title and its sections in reading order."""

    title: str
    sections: tuple[GuideSection, ...]


def parse_guide(markdown: str) -> GuideDocument:
    """Read the guide's markdown into its title and its sections."""
    title = ""
    heading = ""
    blocks: list[GuideBlock] = []
    sections: list[GuideSection] = []
    for chunk in _chunks(markdown.splitlines()):
        first = chunk[0]
        if first.startswith(_SECTION_PREFIX):
            sections.append(GuideSection(heading, tuple(blocks)))
            heading = first[len(_SECTION_PREFIX) :].strip()
            blocks = []
        elif first.startswith(_TITLE_PREFIX):
            title = first[len(_TITLE_PREFIX) :].strip()
        else:
            blocks.extend(_blocks(chunk))
    sections.append(GuideSection(heading, tuple(blocks)))
    kept = tuple(section for section in sections if section.heading or section.blocks)
    return GuideDocument(title, kept)


def _chunks(lines: list[str]) -> Iterator[list[str]]:
    """Group the lines into blocks.

    A blank line parts two blocks, a heading stands alone and a fence keeps
    every line up to its closing fence, blank ones included.
    """
    chunk: list[str] = []
    in_fence = False
    for line in lines:
        fence = line.startswith(_FENCE)
        if in_fence:
            chunk.append(line)
            if fence:
                in_fence = False
                yield chunk
                chunk = []
            continue
        heading = line.startswith((_TITLE_PREFIX, _SECTION_PREFIX))
        if fence or heading or not line.strip():
            if chunk:
                yield chunk
            chunk = []
        if fence:
            in_fence = True
            chunk.append(line)
        elif heading:
            yield [line]
        elif line.strip():
            chunk.append(line)
    if chunk:
        yield chunk


def _blocks(chunk: list[str]) -> list[GuideBlock]:
    """Classify one chunk: a fence, a list, a picture entry or prose."""
    first = chunk[0]
    if first.startswith(_FENCE):
        closed = len(chunk) > 1 and chunk[-1].startswith(_FENCE)
        body = chunk[1:-1] if closed else chunk[1:]
        return [GuideCode("\n".join(body))]
    if first.startswith(_BULLET):
        return [GuideRule(*_split_lead(item)) for item in _items(chunk)]
    lines = list(chunk)
    pictures: list[str] = []
    while lines and (match := _PICTURE.match(lines[0].strip())):
        pictures.append(match["path"])
        lines.pop(0)
    text = _joined(lines)
    if pictures:
        return [GuideEntry(tuple(pictures), *_split_lead(text))]
    return [GuideParagraph(text)]


def _items(chunk: list[str]) -> list[str]:
    """Each bullet item's text, its indented continuation lines joined on."""
    items: list[list[str]] = []
    for line in chunk:
        if line.startswith(_BULLET):
            items.append([line[len(_BULLET) :]])
        else:
            items[-1].append(line)
    return [_joined(item) for item in items]


def _joined(lines: list[str]) -> str:
    """Source lines joined into one line of prose."""
    return " ".join(line.strip() for line in lines)


def _split_lead(text: str) -> tuple[str, str]:
    """The bold lead and the rest; an empty lead when the text opens without one."""
    match = _LEAD.match(text)
    if match is None:
        return "", text
    return match["name"], match["text"]


def inline_html(text: str) -> str:
    """Escape one line of prose, then mark its bold and code spans.

    Code spans are cut out first so a pair of asterisks inside one stays
    literal, as it does on GitHub.
    """
    parts = _CODE_SPAN.split(text)
    out: list[str] = []
    for index, part in enumerate(parts):
        if index % 2:
            out.append(f"<code>{html.escape(part)}</code>")
        else:
            out.append(_BOLD.sub(r"<b>\1</b>", html.escape(part)))
    return "".join(out)


def guide_html(document: GuideDocument, code_background: str) -> str:
    """Draw the guide as Qt rich text, each picture in a column beside its name.

    `code_background` is the active theme's surface colour, so a command block
    reads as set apart in either theme.
    """
    parts = [f"<h2>{inline_html(document.title)}</h2>"] if document.title else []
    for section in document.sections:
        if section.heading:
            parts.append(f"<hr><h3>{inline_html(section.heading)}</h3>")
        for is_entry, run in groupby(
            section.blocks, key=lambda block: isinstance(block, GuideEntry)
        ):
            if is_entry:
                parts.append(_entry_table(run))
            else:
                parts.extend(_block_html(block, code_background) for block in run)
    return "\n".join(parts)


def _entry_table(run: Iterable[GuideBlock]) -> str:
    """A run of entries as ONE table, so their pictures share one column."""
    rows = "".join(_entry_row(block) for block in run if isinstance(block, GuideEntry))
    return (
        f'<table cellspacing="0" cellpadding="{_ENTRY_CELL_PADDING_PX}">'
        f"{rows}</table>"
    )


def _entry_row(entry: GuideEntry) -> str:
    """One entry: its pictures stacked on the left, its sentence on the right.

    Aligned to the top rather than centred, so a sentence that wraps keeps its
    picture beside its first line.
    """
    pictures = "<br>".join(
        f'<img src="{html.escape(path)}">' for path in entry.pictures
    )
    return (
        f'<tr><td valign="top">{pictures}</td>'
        f'<td valign="top">{_lead_html(entry.name, entry.text)}</td></tr>'
    )


def _block_html(block: GuideBlock, code_background: str) -> str:
    """A rule, a command block or a paragraph as rich text."""
    if isinstance(block, GuideCode):
        return (
            f'<table width="100%" cellspacing="0" '
            f'cellpadding="{_CODE_CELL_PADDING_PX}" bgcolor="{code_background}">'
            f"<tr><td><pre>{html.escape(block.text)}</pre></td></tr></table>"
        )
    if isinstance(block, GuideRule):
        return f"<p>{_lead_html(block.name, block.text)}</p>"
    return f"<p>{inline_html(block.text)}</p>"


def _lead_html(name: str, text: str) -> str:
    """A bold name followed by its text; the text alone when there is no name."""
    if not name:
        return inline_html(text)
    return f"<b>{inline_html(name)}</b> {inline_html(text)}"
