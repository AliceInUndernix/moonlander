"""Dotterel dark theme: a Plover extension that makes the Qt GUI dark.

Plover 5.4 has a built-in Dark appearance on Windows and macOS, but on Linux
it is hidden because Qt's colour-scheme hint does nothing there. This
extension instead switches Qt to the Fusion style with a dark palette, which
works on every platform, including dwm/X11.

Enable it in Plover: Configure > Plugins > tick "dotterel_dark_theme".
"""

from plover import log

try:  # Plover 5 (PySide6)
    from PySide6 import QtCore, QtGui, QtWidgets
except ImportError:  # Plover 4 (PyQt5)
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets
    except ImportError:  # no Qt at all (plover --gui none)
        QtCore = QtGui = QtWidgets = None

# Colours (hex). Tweak here.
WINDOW = "#1e1f22"
BASE = "#16171a"        # text fields, tables, paper tape
ALT_BASE = "#232428"
TEXT = "#e6e6e6"
DISABLED_TEXT = "#7a7d85"
BUTTON = "#2b2d31"
HIGHLIGHT = "#d4a017"   # goldenrod, same as the Moonlander steno layer LEDs
HIGHLIGHTED_TEXT = "#16171a"
LINK = "#e3b341"
TOOLTIP_BASE = "#2b2d31"


def _dark_palette():
    QColor, QPalette = QtGui.QColor, QtGui.QPalette

    p = QPalette()
    R, G = QPalette.ColorRole, QPalette.ColorGroup
    for role, colour in (
        (R.Window, WINDOW),
        (R.WindowText, TEXT),
        (R.Base, BASE),
        (R.AlternateBase, ALT_BASE),
        (R.Text, TEXT),
        (R.PlaceholderText, DISABLED_TEXT),
        (R.Button, BUTTON),
        (R.ButtonText, TEXT),
        (R.BrightText, "#ffffff"),
        (R.Highlight, HIGHLIGHT),
        (R.HighlightedText, HIGHLIGHTED_TEXT),
        (R.Link, LINK),
        (R.LinkVisited, LINK),
        (R.ToolTipBase, TOOLTIP_BASE),
        (R.ToolTipText, TEXT),
        (R.Light, "#3a3c42"),
        (R.Midlight, "#313338"),
        (R.Mid, "#26282c"),
        (R.Dark, "#111214"),
        (R.Shadow, "#000000"),
    ):
        p.setColor(role, QColor(colour))
    for role in (R.WindowText, R.Text, R.ButtonText):
        p.setColor(G.Disabled, role, QColor(DISABLED_TEXT))
    return p


def apply_dark_theme(app):
    app.setStyle("Fusion")
    app.setPalette(_dark_palette())
    try:
        # Tells Qt widgets that check the scheme (Qt 6.8+) that we are dark.
        app.styleHints().setColorScheme(QtCore.Qt.ColorScheme.Dark)
    except AttributeError:
        pass


class DarkTheme:
    def __init__(self, engine):
        self._engine = engine
        self._previous = None
        self._context = None

    def _run_in_gui_thread(self, func):
        if QtWidgets is None:
            log.info("dotterel_dark_theme: no Qt, nothing to do")
            return
        QObject, QTimer = QtCore.QObject, QtCore.QTimer
        app = QtWidgets.QApplication.instance()
        if app is None:
            log.info("dotterel_dark_theme: no Qt GUI running, nothing to do")
            return
        # A QObject living in the GUI thread, so the timer fires there even if
        # Plover starts extensions from its engine thread.
        self._context = QObject()
        self._context.moveToThread(app.thread())
        QTimer.singleShot(0, self._context, lambda: func(app))

    def start(self):
        def apply(app):
            self._previous = (app.style().name(), app.palette())
            apply_dark_theme(app)
            log.info("dotterel_dark_theme: dark theme on")

        self._run_in_gui_thread(apply)

    def stop(self):
        previous = self._previous
        if previous is None:
            return

        def restore(app):
            style, palette = previous
            app.setStyle(style)
            app.setPalette(palette)
            try:
                app.styleHints().unsetColorScheme()
            except AttributeError:
                pass

        self._run_in_gui_thread(restore)
