"""The dialogs behind the Help button: documentation, licence and about.

These were methods on MainWindow, which put four dialog bodies inside the class
that owns the tabs and the device notifier. It also took that module half
again over the module size limit. They are plain functions taking the parent widget,
because none of them needs anything from the window except somewhere to sit.

Author: Oliver Ernster
"""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from src import __version__
from src.presentation.views.resource_paths import APP_ICON_PNG, resource_path

# Icon size used by every dialog that shows the app icon.
ICON_PX = 64
# Inset of the floating icon overlay from the dialog's top-right corner.
OVERLAY_MARGIN_PX = 10
OVERLAY_RIGHT_OFFSET_PX = 84

# Body font for the markdown viewers: 1.3x the base size rather than 1.5x.
VIEWER_FONT_CSS = "font-size: 11.7pt;"

OVERLAY_CSS = """
                background-color: rgba(42, 42, 42, 200);
                padding: 5px;
                border-radius: 5px;
            """

DEV_DOCS_HTML = """
<h3>Available Documentation</h3>

<p><b>📘 Development README</b><br>
<a href="file:///DEVELOPMENT_README.md">DEVELOPMENT_README.md</a><br>
Setting up the development environment, running from source, building the application, the checks and the release steps.</p>

<p><b>💻 CLI Usage Reference</b><br>
<a href="file:///CLI_USAGE.md">CLI_USAGE.md</a><br>
Complete command-line interface reference for automation and scripting.</p>

<p><b>🏗️ Architecture</b><br>
<a href="file:///ARCHITECTURE.md">ARCHITECTURE.md</a><br>
The layers, the dependency direction, the execution flow and the enforced invariants.</p>

<hr>

<p><i>Note: Click on any link above to open the documentation file. These files are located in the project root directory.</i></p>
"""

ABOUT_HTML = """
<p><b>Features:</b></p>
<ul>
<li>Quick profile switching</li>
<li>Command-line interface for automation</li>
<li>Stream Deck integration</li>
<li>Profile management</li>
</ul>
<p><b>License:</b> GNU Lesser General Public License v3.0 (LGPL-3.0)</p>
<p>Copyright (C) 2024-2026 Oliver Ernster</p>
<p>For more information, select <b>Help > View License</b> or <b>Help > View Documentation</b>.</p>"""


def _scaled_app_icon() -> QPixmap | None:
    """Return the app icon scaled for a dialog, else None when it is missing."""
    icon_path = resource_path(APP_ICON_PNG)
    if not icon_path.exists():
        return None
    return QPixmap(str(icon_path)).scaled(
        ICON_PX,
        ICON_PX,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _add_header_icon(header_layout: QHBoxLayout) -> None:
    """Add the app icon to the right of a dialog header, when it resolves."""
    pixmap = _scaled_app_icon()
    if pixmap is None:
        return
    icon_label = QLabel()
    icon_label.setPixmap(pixmap)
    icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
    header_layout.addWidget(icon_label)


def _add_overlay_icon(dialog: QDialog) -> None:
    """Float the app icon over a dialog's top-right corner, when it resolves."""
    pixmap = _scaled_app_icon()
    if pixmap is None:
        return
    icon_label = QLabel(dialog)
    icon_label.setPixmap(pixmap)
    icon_label.setFixedSize(ICON_PX, ICON_PX)
    icon_label.setStyleSheet(OVERLAY_CSS)
    icon_label.setScaledContents(False)

    def position_icon() -> None:
        icon_label.move(dialog.width() - OVERLAY_RIGHT_OFFSET_PX, OVERLAY_MARGIN_PX)
        icon_label.raise_()

    # Position once the dialog has been laid out.
    QTimer.singleShot(0, position_icon)


def _add_close_button(dialog: QDialog, layout: QVBoxLayout) -> None:
    """Add the Close button every one of these dialogs ends with."""
    close_button = QPushButton("Close")
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)


def _read_bundled_text(
    parent: QWidget, path: Path, subject: str, missing_title: str
) -> str | None:
    """Return a bundled text file's contents, reporting failure to the user.

    Returns None when the file is absent or unreadable, having already shown
    the message, so the caller simply stops.
    """
    if not path.exists():
        QMessageBox.warning(
            parent,
            missing_title,
            f"{subject} file not found. Please check the installation.",
        )
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as error:
        # Falls back to showing nothing: the file exists but cannot be read,
        # which is a broken installation rather than something recoverable.
        QMessageBox.critical(parent, "Error", f"Failed to read {subject}: {error}")
        return None


def show_documentation(parent: QWidget) -> None:
    """Show the documentation viewer dialog."""
    readme_content = _read_bundled_text(
        parent,
        resource_path("README.md"),
        "README.md",
        "Documentation Not Found",
    )
    if readme_content is None:
        return

    dialog = QDialog(parent)
    dialog.setWindowTitle("Audio Deck Documentation")
    dialog.setMinimumSize(800, 600)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(0, 0, 0, 0)

    text_browser = QTextBrowser()
    text_browser.setOpenExternalLinks(True)
    text_browser.setStyleSheet(VIEWER_FONT_CSS)
    text_browser.setMarkdown(readme_content)
    layout.addWidget(text_browser)

    _add_overlay_icon(dialog)
    _add_close_button(dialog, layout)

    dialog.exec()


def _show_dev_doc_file(dialog: QDialog, file_name: str) -> None:
    """Open one development document in a child viewer dialog."""
    content = _read_bundled_text(
        dialog, resource_path(file_name), file_name, "File Not Found"
    )
    if content is None:
        return

    file_dialog = QDialog(dialog)
    file_dialog.setWindowTitle(f"Audio Deck - {file_name}")
    file_dialog.setMinimumSize(800, 600)

    file_layout = QVBoxLayout(file_dialog)

    file_browser = QTextBrowser()
    file_browser.setOpenExternalLinks(True)
    file_browser.setStyleSheet(VIEWER_FONT_CSS)
    file_browser.setMarkdown(content)
    file_layout.addWidget(file_browser)

    _add_close_button(file_dialog, file_layout)

    file_dialog.exec()


def show_dev_documentation(parent: QWidget) -> None:
    """Show the development documentation dialog with links to dev files."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Development Documentation")
    dialog.setMinimumSize(700, 500)

    layout = QVBoxLayout(dialog)

    header_layout = QHBoxLayout()
    left_layout = QVBoxLayout()

    title_label = QLabel("<h2>Development Documentation</h2>")
    title_label.setTextFormat(Qt.TextFormat.RichText)
    left_layout.addWidget(title_label)

    desc_label = QLabel(
        "<p>Technical documentation for developers and advanced users.</p>"
    )
    desc_label.setTextFormat(Qt.TextFormat.RichText)
    left_layout.addWidget(desc_label)

    header_layout.addLayout(left_layout)
    header_layout.addStretch()
    _add_header_icon(header_layout)
    layout.addLayout(header_layout)

    text_browser = QTextBrowser()
    text_browser.setOpenExternalLinks(False)
    text_browser.setHtml(DEV_DOCS_HTML)

    def handle_link_click(url: QUrl) -> None:
        _show_dev_doc_file(dialog, url.toString().replace("file:///", ""))
        # Restore the link list after the child dialog closes.
        text_browser.setHtml(DEV_DOCS_HTML)

    text_browser.anchorClicked.connect(handle_link_click)
    layout.addWidget(text_browser)

    _add_close_button(dialog, layout)

    dialog.exec()


def show_license(parent: QWidget) -> None:
    """Show the License dialog."""
    license_content = _read_bundled_text(
        parent, resource_path("LICENSE"), "LICENSE", "License Not Found"
    )
    if license_content is None:
        return

    dialog = QDialog(parent)
    dialog.setWindowTitle("License - GNU LGPL v3.0")
    dialog.setMinimumSize(800, 600)

    layout = QVBoxLayout(dialog)

    text_browser = QTextBrowser()
    text_browser.setPlainText(license_content)
    layout.addWidget(text_browser)

    _add_close_button(dialog, layout)

    dialog.exec()


def show_about(parent: QWidget) -> None:
    """Show the About dialog."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("About Audio Deck")
    dialog.setMinimumSize(500, 400)

    layout = QVBoxLayout(dialog)

    header_layout = QHBoxLayout()
    left_layout = QVBoxLayout()

    title_label = QLabel("<h2>Audio Deck</h2>")
    title_label.setTextFormat(Qt.TextFormat.RichText)
    left_layout.addWidget(title_label)

    version_label = QLabel(f"<p><b>Version:</b> {__version__}</p>")
    version_label.setTextFormat(Qt.TextFormat.RichText)
    left_layout.addWidget(version_label)

    author_label = QLabel("<p><b>Author:</b> Oliver Ernster</p>")
    author_label.setTextFormat(Qt.TextFormat.RichText)
    left_layout.addWidget(author_label)

    header_layout.addLayout(left_layout)
    header_layout.addStretch()
    _add_header_icon(header_layout)
    layout.addLayout(header_layout)

    subtitle_label = QLabel(
        "<p>A professional audio device switcher for Windows with Stream Deck "
        "integration.</p>"
    )
    subtitle_label.setTextFormat(Qt.TextFormat.RichText)
    subtitle_label.setWordWrap(True)
    layout.addWidget(subtitle_label)

    text_label = QLabel(ABOUT_HTML)
    text_label.setTextFormat(Qt.TextFormat.RichText)
    text_label.setWordWrap(True)
    layout.addWidget(text_label)

    _add_close_button(dialog, layout)

    dialog.exec()
