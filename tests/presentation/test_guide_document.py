"""The Guide reads DOCUMENTATION.md into sections and draws every word of it.

The file stays the one home of the guide's words, so the promise that matters
is that restructuring lost nothing: every word of the markdown reaches the page
in the same order and every picture it names is drawn. The rest pins the parse
of each construct the guide uses, plus the Help menu entry that opens it.
"""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtWidgets import QMenu, QTextBrowser

from src.presentation.views import theme
from src.presentation.views.help_button import build_help_button
from src.presentation.views.help_dialogs import build_guide_dialog
from src.presentation.widgets.guide_document import (
    GuideCode,
    GuideDocument,
    GuideEntry,
    GuideParagraph,
    GuideRule,
    GuideSection,
    guide_html,
    inline_html,
    parse_guide,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GUIDE_TEXT = (PROJECT_ROOT / "DOCUMENTATION.md").read_text(encoding="utf-8")

# Qt stands this character in for every picture in a document's plain text.
OBJECT_REPLACEMENT = "\ufffc"

SURFACE = theme.tokens_for(theme.THEME_DARK)["surface"]


def _noop() -> None:
    """A handler that does nothing, for a menu under test."""


def _markdown_words(markdown: str) -> list[str]:
    """The words a reader sees in the markdown, its syntax removed by hand.

    Written apart from the parser so the comparison cannot pass by agreeing
    with itself.
    """
    words: list[str] = []
    for line in markdown.splitlines():
        if line.startswith(("![](", "```")):
            continue
        line = re.sub(r"^(#+|-) ", "", line)
        words.extend(line.replace("**", "").replace("`", "").split())
    return words


def _plain_words(browser: QTextBrowser) -> list[str]:
    """The words a browser shows, pictures left out."""
    return browser.toPlainText().replace(OBJECT_REPLACEMENT, " ").split()


def _page_words(markup: str) -> list[str]:
    """The words a page of rich text shows."""
    browser = QTextBrowser()
    browser.setHtml(markup)
    return _plain_words(browser)


def test_every_word_of_the_file_reaches_the_guide(qapp) -> None:
    """Same words, same order: the restructure dropped nothing."""
    markup = guide_html(parse_guide(GUIDE_TEXT), SURFACE)

    assert _page_words(markup) == _markdown_words(GUIDE_TEXT)


def test_every_picture_the_file_names_is_drawn_in_order() -> None:
    """A picture named in the file and missing from the page is a lost key."""
    named = re.findall(r"^!\[\]\(([^)]+)\)$", GUIDE_TEXT, flags=re.MULTILINE)
    drawn = re.findall(
        r'<img src="([^"]+)">', guide_html(parse_guide(GUIDE_TEXT), SURFACE)
    )

    assert named, "the guide names no pictures at all"
    assert drawn == named


def test_a_run_of_entries_shares_one_picture_column() -> None:
    """Consecutive entries form one table; prose between them starts another."""
    markdown = (
        "## Keys\n\n![](a.png)\n**One.** first\n\n"
        "![](b.png)\n![](c.png)\n**Two.** second\n\nBetween.\n\n"
        "![](d.png)\n**Three.** third\n"
    )

    document = parse_guide(markdown)
    markup = guide_html(document, SURFACE)

    assert document == GuideDocument(
        "",
        (
            GuideSection(
                "Keys",
                (
                    GuideEntry(("a.png",), "One.", "first"),
                    GuideEntry(("b.png", "c.png"), "Two.", "second"),
                    GuideParagraph("Between."),
                    GuideEntry(("d.png",), "Three.", "third"),
                ),
            ),
        ),
    )
    assert markup.count("<table") == 2
    assert '<img src="b.png"><br><img src="c.png">' in markup
    assert "<b>One.</b> first" in markup


def test_the_title_and_opening_prose_come_before_the_first_heading() -> None:
    """A heading needs no blank line after it; an empty section still shows."""
    document = parse_guide("# Title\nIntro one\nline two\n\n## Empty\n")
    markup = guide_html(document, SURFACE)

    assert document == GuideDocument(
        "Title",
        (
            GuideSection("", (GuideParagraph("Intro one line two"),)),
            GuideSection("Empty", ()),
        ),
    )
    assert markup.startswith("<h2>Title</h2>")
    assert "<hr><h3>Empty</h3>" in markup


def test_a_document_without_a_title_draws_no_title_heading() -> None:
    """Prose alone is drawn as prose."""
    markup = guide_html(parse_guide("Just prose.\n"), SURFACE)

    assert markup == "<p>Just prose.</p>"


def test_bullets_become_rules_carrying_their_continuation_lines() -> None:
    """A bold lead becomes the rule's name; an item without one keeps its text."""
    document = parse_guide("- **Bold claim.** what it\n  means\n- no lead here\n")
    markup = guide_html(document, SURFACE)

    assert document.sections[0].blocks == (
        GuideRule("Bold claim.", "what it means"),
        GuideRule("", "no lead here"),
    )
    assert "<p><b>Bold claim.</b> what it means</p>" in markup
    assert "<p>no lead here</p>" in markup


def test_an_entry_without_a_bold_lead_keeps_its_text() -> None:
    """The picture still leads; the sentence is drawn without a bold name."""
    document = parse_guide("![](a.png)\nplain words\n")

    assert document.sections[0].blocks == (GuideEntry(("a.png",), "", "plain words"),)
    assert '<td valign="top">plain words</td>' in guide_html(document, SURFACE)


def test_a_fence_keeps_its_lines_and_parts_the_prose_round_it() -> None:
    """Spacing and blank lines survive; markup inside the fence is escaped."""
    document = parse_guide("Before\n```\nkeep   spacing\n\n<tag>\n```\nAfter\n")
    markup = guide_html(document, SURFACE)

    assert document.sections[0].blocks == (
        GuideParagraph("Before"),
        GuideCode("keep   spacing\n\n<tag>"),
        GuideParagraph("After"),
    )
    assert "<pre>keep   spacing\n\n&lt;tag&gt;</pre>" in markup
    assert f'bgcolor="{SURFACE}"' in markup


def test_an_unclosed_fence_runs_to_the_end_of_the_file() -> None:
    """A missing closing fence keeps what there is rather than dropping it."""
    assert parse_guide("```\nopen\n").sections[0].blocks == (GuideCode("open"),)


def test_inline_markup_escapes_first_and_leaves_code_spans_literal() -> None:
    """Asterisks inside a code span stay asterisks, as they do on GitHub."""
    assert inline_html("a **b** `**c** <d>` & e") == (
        "a <b>b</b> <code>**c** &lt;d&gt;</code> &amp; e"
    )


def test_the_help_menu_leads_with_the_guide(qapp) -> None:
    """The entry is named Guide; the old name is gone."""
    button = build_help_button(_noop, _noop, _noop, _noop, _noop)
    menu = button.findChild(QMenu)
    titles = [action.text() for action in menu.actions() if not action.isSeparator()]

    assert titles[0] == "Guide"
    assert "View Documentation" not in titles


def test_the_guide_dialog_draws_the_whole_file(qapp) -> None:
    """The dialog the menu opens carries the same words as the file."""
    dialog = build_guide_dialog(None, GUIDE_TEXT)
    browser = dialog.findChild(QTextBrowser)

    assert dialog.windowTitle() == "Audio Deck Guide"
    assert _plain_words(browser) == _markdown_words(GUIDE_TEXT)
