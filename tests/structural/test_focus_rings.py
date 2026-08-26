"""Structural tests keeping the focus ring on controls, never on regions.

Three faults are scanned for, all in the stylesheet sources.

A ring selector that names a CONTAINER (or the universal selector) reaches
every pane in the app, because a Qt QSS class selector matches every
subclass: `QFrame:focus` lands a border on every scroll area, list, table
and label there is.

A `:hover` ring on a REGION follows the mouse rather than marking a target.
A control is pointed AT, so a ring under the pointer says what is about to
be pressed; a region is pointed INTO, so the pointer rests inside it for as
long as the view is open.

ANY ring on an ITEM VIEW, hovered or focused, is wrong. Both were a real
defect: pointing at the profile list ringed the whole list. So did
clicking the empty space below the last profile, which ringed everything
while selecting nothing. An item view needs no ring, because its current
item already shows where the user is.

An object name excuses the first fault, because it proves the rule was aimed
at one widget on purpose. It excuses neither of the others, since scoping a
rule to one named list changes nothing about how that list behaves.

The scan is static on purpose. An offscreen pixel diff cannot settle what a
focus ring paints: a focused QPushButton diffs to zero changed pixels under
every style tried, so a clean diff proves nothing.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STYLESHEET_ROOTS = (PROJECT_ROOT / "src", PROJECT_ROOT / "installer")

# Selectors that reach a container, whether the author meant them to or not.
CONTAINER_SELECTORS = frozenset(
    {
        "*",
        "QWidget",
        "QFrame",
        "QAbstractScrollArea",
        "QScrollArea",
        "QGroupBox",
        "QStackedWidget",
        "QSplitter",
        "QTabWidget",
    }
)

# An ITEM VIEW draws no ring in ANY state. Its current item already carries
# the indication: focusing a list paints the current row without a single
# stylesheet rule, then moving with the arrows selects. A rectangle round the
# whole view adds nothing and fires on a click into the empty space below the
# items, ringing everything while selecting nothing.
ITEM_VIEW_SELECTORS = frozenset(
    {
        "QAbstractItemView",
        "QListView",
        "QListWidget",
        "QTableView",
        "QTableWidget",
        "QTreeView",
        "QTreeWidget",
        "QColumnView",
    }
)

# Any other widget the pointer rests INSIDE. A scrolling region with no items
# has nothing but a ring to show focus with, so it keeps the focus half and
# loses only hover.
REGION_SELECTORS = ITEM_VIEW_SELECTORS | frozenset(
    {
        "*",
        "QWidget",
        "QFrame",
        "QGroupBox",
        "QStackedWidget",
        "QScrollArea",
        "QAbstractScrollArea",
        "QTextBrowser",
        "QTextEdit",
        "QPlainTextEdit",
        "QGraphicsView",
    }
)

# A ring is a visible border or outline. These values paint nothing, so a rule
# setting one of them is suppressing an indicator rather than drawing one.
RING_PROPERTIES = ("border", "outline")
INVISIBLE_VALUES = ("none", "0", "0px", "transparent", "initial", "unset")

_BLOCK = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
_DECLARATION = re.compile(r"([a-z-]+)\s*:\s*([^;]+)")


def _normalise(text: str) -> str:
    """Turn an f-string stylesheet into plain QSS without moving an offset.

    Every substitution keeps the original length, so a match offset still
    maps to the right source line. A stylesheet string either doubles its
    braces throughout or uses none, so one test settles which.
    """
    if "{{" not in text:
        return text
    marked = text.replace("{{", "{\x00").replace("}}", "}\x00")
    marked = re.sub(
        r"\{(?![\x00])[^{}]*\}",
        lambda match: "V" * len(match.group(0)),
        marked,
    )
    return marked.replace("\x00", " ")


def _paints_a_ring(body: str) -> bool:
    for prop, value in _DECLARATION.findall(body):
        if not prop.startswith(RING_PROPERTIES):
            continue
        cleaned = value.strip().strip(";").lower()
        if cleaned and not any(cleaned.startswith(v) for v in INVISIBLE_VALUES):
            return True
    return False


def _clean_selector(part: str) -> str:
    """Strip the host language off a selector lifted out of a source file.

    The block pattern captures back to the previous closing brace, so the
    first selector in a file drags the assignment and the opening quotes
    with it. A real selector never contains a quote.
    """
    tail = part.strip().splitlines()[-1] if part.strip() else ""
    for marker in ('"""', "'''", '"', "'", "="):
        if marker in tail:
            tail = tail.rsplit(marker, 1)[-1]
    return " ".join(tail.split())


def _selector_parts(selector: str, state: str):
    for raw in selector.split(","):
        part = _clean_selector(raw)
        if part and state in part:
            yield part


def _base_names(part: str):
    """Yield (class, token) for each element of a selector.

    A subcontrol (``::indicator``, ``::item``) is skipped: it is a control
    drawn inside the view rather than the view itself, so it rings like any
    other control.
    """
    for token in re.split(r"[\s>]+", part):
        token = token.strip()
        if "::" in token:
            continue
        yield re.split(r"[:#\[]", token)[0], token


def container_ring_offences(text: str, where: str) -> list[str]:
    """Ring rules whose selector reaches a container, in one source."""
    found = []
    normalised = _normalise(text)
    for match in _BLOCK.finditer(normalised):
        if not _paints_a_ring(match.group(2)):
            continue
        line = normalised.count("\n", 0, match.start(2)) + 1
        for state in (":focus", ":hover"):
            for part in _selector_parts(match.group(1), state):
                for base, token in _base_names(part):
                    if "#" in token:
                        continue
                    if base in CONTAINER_SELECTORS:
                        found.append(f"{where}:{line}: {part}")
    return found


def region_hover_offences(text: str, where: str) -> list[str]:
    """Hover rings on a region, in one source. An object name is no excuse."""
    found = []
    normalised = _normalise(text)
    for match in _BLOCK.finditer(normalised):
        if not _paints_a_ring(match.group(2)):
            continue
        line = normalised.count("\n", 0, match.start(2)) + 1
        for part in _selector_parts(match.group(1), ":hover"):
            for base, _token in _base_names(part):
                if base in REGION_SELECTORS:
                    found.append(f"{where}:{line}: {part}")
    return found


def item_view_ring_offences(text: str, where: str) -> list[str]:
    """Any ring on an item view, hovered or focused, in one source."""
    found = []
    normalised = _normalise(text)
    for match in _BLOCK.finditer(normalised):
        if not _paints_a_ring(match.group(2)):
            continue
        line = normalised.count("\n", 0, match.start(2)) + 1
        for state in (":hover", ":focus"):
            for part in _selector_parts(match.group(1), state):
                for base, _token in _base_names(part):
                    if base in ITEM_VIEW_SELECTORS:
                        found.append(f"{where}:{line}: {part}")
    return found


def _stylesheet_sources():
    for root in STYLESHEET_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            yield path, path.read_text(encoding="utf-8")


def test_no_ring_selector_reaches_a_container() -> None:
    """No focus or hover ring is styled onto a pane."""
    offences = []
    for path, text in _stylesheet_sources():
        offences.extend(
            container_ring_offences(text, str(path.relative_to(PROJECT_ROOT)))
        )
    assert not offences, "ring selectors reaching a container:\n" + "\n".join(offences)


def test_no_region_rings_on_hover() -> None:
    """No list, table, tree, text view or scroll area rings under the mouse."""
    offences = []
    for path, text in _stylesheet_sources():
        offences.extend(
            region_hover_offences(text, str(path.relative_to(PROJECT_ROOT)))
        )
    assert not offences, "regions ringing on hover:\n" + "\n".join(offences)


def test_no_item_view_rings_in_any_state() -> None:
    """No list, table or tree draws a rectangle round itself, ever."""
    offences = []
    for path, text in _stylesheet_sources():
        offences.extend(
            item_view_ring_offences(text, str(path.relative_to(PROJECT_ROOT)))
        )
    assert not offences, "item views drawing a ring:\n" + "\n".join(offences)


def test_the_item_view_guard_bites() -> None:
    """A planted item-view ring is reported on hover and on focus alike."""
    hovered = 'S = f"""\nQListWidget:enabled:hover {{ border-color: {ring}; }}\n"""'
    assert item_view_ring_offences(hovered, "hovered")
    focused = 'S = f"""\nQListWidget:enabled:focus {{ border-color: {ring}; }}\n"""'
    assert item_view_ring_offences(focused, "focused")
    other = 'S = f"""\nQPushButton:enabled:focus {{ border-color: {ring}; }}\n"""'
    assert not item_view_ring_offences(other, "other")


def test_the_container_guard_bites() -> None:
    """A planted container ring is reported; a scoped one is not."""
    planted = 'S = f"""\nQFrame:focus {{ border: 2px solid {ring}; }}\n"""'
    assert container_ring_offences(planted, "planted")
    scoped = (
        'S = f"""\nQScrollArea#View:enabled:focus {{ border: 2px solid {r}; }}\n"""'
    )
    assert not container_ring_offences(scoped, "scoped")


def test_the_hover_guard_bites() -> None:
    """A planted region hover is reported, object name or not."""
    planted = 'S = f"""\nQListWidget:enabled:hover {{ border-color: {ring}; }}\n"""'
    assert region_hover_offences(planted, "planted")
    named = 'S = f"""\nQListWidget#Profiles:enabled:hover {{ border-color: {r}; }}\n"""'
    assert region_hover_offences(named, "named")
    focused = 'S = f"""\nQListWidget:enabled:focus {{ border-color: {ring}; }}\n"""'
    assert not region_hover_offences(focused, "focused")
