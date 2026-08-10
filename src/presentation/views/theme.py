"""Theme facility: token dicts, stylesheet and palette builders, persistence.

Two semantic token dicts (dark is the Catppuccin Mocha set the app has worn
since the Linux port; light is its Latte counterpart) feed one stylesheet
template and one palette builder, so the three-state ring model (no ring at
rest, green on hover or focus while enabled, permanent red while disabled)
holds in every theme by construction. The ring tokens are per theme: the
pastel green that reads on near-black is weak on white, so light carries a
saturated green and a saturated red instead.

The active theme name rides as a dynamic property on the QApplication (no
module-level state) and persists to a JSON settings file whose path the
composition root passes in, beside the profiles. Widgets that resolve
colours in code rather than through the app stylesheet expose a `restyle()`
method and are called after every switch.
"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

THEME_DARK = "dark"
THEME_LIGHT = "light"

_THEME_KEY = "theme"
_APP_THEME_PROPERTY = "audiodeck_theme"

# The glyph shows the mode a press switches TO, not the current one.
TOGGLE_BUTTON_OBJECT_NAME = "ThemeToggleButton"
_TOGGLE_GLYPHS = {THEME_DARK: "☀️", THEME_LIGHT: "\U0001f319"}
_TOGGLE_TOOLTIPS = {
    THEME_DARK: "Switch to light mode",
    THEME_LIGHT: "Switch to dark mode",
}

# Catppuccin Mocha, matching the project site.
_DARK: dict[str, str] = {
    "window_bg": "#1e1e2e",
    "surface": "#313244",
    "field_bg": "#181825",
    "text": "#cdd6f4",
    "text_muted": "#6c7086",
    "accent": "#7b5caa",
    "link": "#89b4fa",
    "separator": "#45475a",
    "ring": "#a6e3a1",
    "danger": "#f38ba8",
}

# Catppuccin Latte, with saturated ring and danger tokens so the two rings
# keep their contrast against light surfaces.
_LIGHT: dict[str, str] = {
    "window_bg": "#eff1f5",
    "surface": "#dce0e8",
    "field_bg": "#ffffff",
    "text": "#4c4f69",
    "text_muted": "#6c6f85",
    "accent": "#8839ef",
    "link": "#1e66f5",
    "separator": "#bcc0cc",
    "ring": "#059669",
    "danger": "#dc2626",
}

_TOKENS = {THEME_DARK: _DARK, THEME_LIGHT: _LIGHT}


def tokens_for(name: str) -> dict[str, str]:
    """Return the token dict for `name`, defaulting to dark."""
    return _TOKENS.get(name, _DARK)


def colours(app: QApplication | None = None) -> dict[str, str]:
    """Return the active theme's tokens, for widgets that style in code."""
    if app is None:
        instance = QApplication.instance()
        app = instance if isinstance(instance, QApplication) else None
    return tokens_for(current_theme(app))


def current_theme(app: QApplication | None) -> str:
    """Return the theme the given QApplication is currently showing."""
    if app is None:
        return THEME_DARK
    name = app.property(_APP_THEME_PROPERTY)
    return name if name in _TOKENS else THEME_DARK


def load_saved_theme(settings_path: Path) -> str:
    """Return the persisted theme name, defaulting to dark."""
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return THEME_DARK
    name = data.get(_THEME_KEY) if isinstance(data, dict) else None
    return name if name in _TOKENS else THEME_DARK


def _save_theme(settings_path: Path, name: str) -> None:
    """Persist `name`, best-effort: the in-session theme applies regardless."""
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        data[_THEME_KEY] = name
        settings_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass


def toggle_glyph(theme_name: str) -> str:
    """Return the sun/moon glyph a toggle button shows under `theme_name`."""
    return _TOGGLE_GLYPHS[theme_name]


def toggle_tooltip(theme_name: str) -> str:
    """Return the toggle button tooltip under `theme_name`."""
    return _TOGGLE_TOOLTIPS[theme_name]


def build_palette(tokens: dict[str, str]) -> QPalette:
    """Build the Fusion palette from one theme's tokens."""
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: tokens["window_bg"],
        QPalette.ColorRole.WindowText: tokens["text"],
        QPalette.ColorRole.Base: tokens["field_bg"],
        QPalette.ColorRole.AlternateBase: tokens["surface"],
        QPalette.ColorRole.Text: tokens["text"],
        QPalette.ColorRole.Button: tokens["surface"],
        QPalette.ColorRole.ButtonText: tokens["text"],
        QPalette.ColorRole.ToolTipBase: tokens["surface"],
        QPalette.ColorRole.ToolTipText: tokens["text"],
        QPalette.ColorRole.PlaceholderText: tokens["text_muted"],
        QPalette.ColorRole.Highlight: tokens["accent"],
        QPalette.ColorRole.HighlightedText: tokens["text"],
        QPalette.ColorRole.BrightText: tokens["text"],
        QPalette.ColorRole.Link: tokens["link"],
    }
    for role, colour in roles.items():
        palette.setColor(role, QColor(colour))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        palette.setColor(
            QPalette.ColorGroup.Disabled, role, QColor(tokens["text_muted"])
        )
    return palette


def build_stylesheet(tokens: dict[str, str]) -> str:
    """Build the application stylesheet from one theme's tokens.

    The 13.5pt base size, the three-state ring model (the ring is the ONLY
    focus indicator, so the native dotted rectangle is suppressed with
    outline: none) and the tray icon rules, all parameterised so both
    themes are the same sheet with different colours.
    """
    return f"""
        * {{
            font-size: 13.5pt;
            outline: none;
        }}
        QToolTip {{
            font-size: 10.5pt;
            color: {tokens["text"]};
            background-color: {tokens["surface"]};
            border: 1px solid {tokens["text_muted"]};
        }}
        QPushButton {{
            font-size: 13.5pt;
            padding: 6px 12px;
            border: 2px solid transparent;
            border-radius: 0;
        }}
        QPushButton:enabled:hover, QPushButton:enabled:focus {{
            border-color: {tokens["ring"]};
        }}
        QPushButton:disabled {{
            border: 2px solid {tokens["danger"]};
            background-color: {tokens["surface"]};
            color: {tokens["text_muted"]};
        }}
        QLineEdit, QComboBox, QListWidget {{
            font-size: 13.5pt;
            padding: 4px;
            border: 2px solid transparent;
            border-radius: 0;
        }}
        QLineEdit:enabled:hover, QLineEdit:enabled:focus,
        QComboBox:enabled:hover, QComboBox:enabled:focus,
        QListWidget:enabled:hover, QListWidget:enabled:focus {{
            border-color: {tokens["ring"]};
        }}
        QLineEdit:disabled, QComboBox:disabled, QListWidget:disabled {{
            border: 2px solid {tokens["danger"]};
            background-color: {tokens["surface"]};
            color: {tokens["text_muted"]};
        }}
        QPushButton#ViewButton, QPushButton#TrayAction,
        QPushButton#ThemeToggleButton, QPushButton#HelpButton {{
            background-color: transparent;
            border: 2px solid transparent;
            border-radius: 4px;
            padding: 0px;
        }}
        QPushButton#ViewButton:enabled:hover,
        QPushButton#ViewButton:enabled:focus,
        QPushButton#TrayAction:enabled:hover,
        QPushButton#TrayAction:enabled:focus,
        QPushButton#ThemeToggleButton:enabled:hover,
        QPushButton#ThemeToggleButton:enabled:focus,
        QPushButton#HelpButton:enabled:hover,
        QPushButton#HelpButton:enabled:focus {{
            background-color: {tokens["surface"]};
            border: 2px solid {tokens["ring"]};
        }}
        QPushButton#ViewButton:disabled, QPushButton#TrayAction:disabled {{
            background-color: transparent;
            border: 2px solid {tokens["danger"]};
        }}
        QFrame#Separator {{
            color: {tokens["separator"]};
        }}
        QGroupBox {{
            font-size: 13.5pt;
            font-weight: bold;
        }}
        QMessageBox {{
            font-size: 13.5pt;
        }}
    """


def apply_theme(app: QApplication, name: str, settings_path: Path) -> None:
    """Restyle the whole app to `name`, persist it and refresh widgets.

    Fusion plus the palette plus the sheet, on every platform: the system
    themes never matched the app's own dark default anyway and one code
    path beats three.
    """
    tokens = tokens_for(name)
    app.setStyle("Fusion")
    app.setPalette(build_palette(tokens))
    app.setStyleSheet(build_stylesheet(tokens))
    app.setProperty(_APP_THEME_PROPERTY, name)
    _save_theme(settings_path, name)
    _restyle_dynamic_widgets(app)


def toggle_theme(app: QApplication, settings_path: Path) -> None:
    """Switch between dark and light at runtime."""
    now = current_theme(app)
    target = THEME_LIGHT if now == THEME_DARK else THEME_DARK
    apply_theme(app, target, settings_path)


def _restyle_dynamic_widgets(app: QApplication) -> None:
    """Ask every widget that paints its own colours to rebuild.

    Most widgets follow the theme through the stylesheet alone. A widget
    whose colours are resolved in code (the Help button's widget-level
    sheet, the theme toggle's glyph) exposes a `restyle()` method and it
    is called here after the switch.
    """
    for widget in app.allWidgets():
        restyle = getattr(widget, "restyle", None)
        if callable(restyle):
            restyle()
