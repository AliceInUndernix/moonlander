"""Qt imports for Plover 5 (PySide6) and Plover 4 (PyQt5)."""

try:  # Plover 5
    from PySide6.QtCore import QEvent, QObject, QPointF, QRectF, Qt, QTimer, QUrl
    from PySide6.QtGui import (QAction, QBrush, QColor, QDesktopServices, QFont, QKeySequence, QPainter,
                               QPainterPath, QPalette, QPen, QShortcut, QTextCursor)
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QFrame,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMenu,
        QMessageBox,
        QSizePolicy,
        QPlainTextEdit,
        QPushButton,
        QScrollArea,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextBrowser,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # Plover 4
    from PyQt5.QtCore import QEvent, QObject, QPointF, QRectF, Qt, QTimer, QUrl
    from PyQt5.QtGui import (QBrush, QColor, QDesktopServices, QFont, QKeySequence, QPainter,
                             QPainterPath, QPalette, QPen, QTextCursor)
    from PyQt5.QtWidgets import (
        QAbstractItemView,
        QAction,
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QFrame,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMenu,
        QMessageBox,
        QSizePolicy,
        QPlainTextEdit,
        QPushButton,
        QScrollArea,
        QShortcut,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextBrowser,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )

__all__ = [
    "QAbstractItemView", "QAction", "QApplication", "QBrush", "QCheckBox",
    "QColor", "QComboBox", "QDesktopServices", "QEvent", "QObject", "QUrl", "QFileDialog", "QFont", "QGridLayout", "QHBoxLayout",
    "QFrame", "QHeaderView", "QKeySequence", "QLabel", "QLineEdit", "QListWidget",
    "QListWidgetItem", "QMenu", "QMessageBox", "QPlainTextEdit", "QPushButton",
    "QScrollArea", "QShortcut", "QSizePolicy", "QSplitter", "QTableWidget", "QTableWidgetItem", "QTabWidget", "QTimer", "QToolButton",
    "QVBoxLayout", "QWidget", "Qt", "QPainter", "QPainterPath", "QPalette", "QPen", "QPointF", "QRectF",
]
