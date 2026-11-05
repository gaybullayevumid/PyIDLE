import os
import shutil
import subprocess
import sys

from PyQt6.QtCore import QDir, QSortFilterProxyModel, Qt, pyqtSignal
from PyQt6.QtGui import QFileSystemModel, QGuiApplication
from PyQt6.QtWidgets import QDockWidget, QInputDialog, QLabel, QMenu, QMessageBox, QTreeView

HIDDEN = {"__pycache__", ".git", "node_modules", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".idea"}


class _Filter(QSortFilterProxyModel):
    def filterAcceptsRow(self, row, parent):
        index = self.sourceModel().index(row, 0, parent)
        return self.sourceModel().fileName(index) not in HIDDEN


class FileExplorer(QDockWidget):
    file_opened = pyqtSignal(str)
    path_deleted = pyqtSignal(str)
    path_renamed = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__("Explorer", parent)
        self.root = None
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)

        title = QLabel("EXPLORER")
        title.setObjectName("explorerTitle")
        self.setTitleBarWidget(title)

        self.model = QFileSystemModel()
        self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot | QDir.Filter.Hidden)
        self.proxy = _Filter()
        self.proxy.setSourceModel(self.model)

        self.tree = QTreeView()
        self.tree.setModel(self.proxy)
        self.tree.setHeaderHidden(True)
        for col in (1, 2, 3):
            self.tree.hideColumn(col)
        self.tree.doubleClicked.connect(self._on_double_click)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._menu)
        self.setWidget(self.tree)

    def set_root(self, folder):
        self.root = os.path.normpath(folder)
        self.model.setRootPath(folder)
        self.tree.setRootIndex(self.proxy.mapFromSource(self.model.index(folder)))
        self.setWindowTitle(folder)

    def _path(self, index):
        return os.path.normpath(self.model.filePath(self.proxy.mapToSource(index)))

    def _on_double_click(self, index):
        path = self._path(index)
        if os.path.isfile(path):
            self.file_opened.emit(path)

    # --- kontekst menyu ---
    def _target_dir(self, index):
        if not index.isValid():
            return self.root
        path = self._path(index)
        return path if os.path.isdir(path) else os.path.dirname(path)

    def _menu(self, pos):
        if not self.root:
            return
        index = self.tree.indexAt(pos)
        path = self._path(index) if index.isValid() else self.root
        menu = QMenu(self)
        menu.addAction("New File", lambda: self._new(self._target_dir(index), folder=False))
        menu.addAction("New Folder", lambda: self._new(self._target_dir(index), folder=True))
        if index.isValid():
            menu.addSeparator()
            menu.addAction("Rename", lambda: self._rename(path))
            menu.addAction("Delete", lambda: self._delete(path))
        menu.addSeparator()
        menu.addAction("Copy Path", lambda: QGuiApplication.clipboard().setText(path))
        menu.addAction("Reveal in File Manager", lambda: self._reveal(path))
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _new(self, parent_dir, folder):
        label = "Papka nomi:" if folder else "Fayl nomi:"
        name, ok = QInputDialog.getText(self, "New Folder" if folder else "New File", label)
        name = name.strip()
        if not ok or not name:
            return
        path = os.path.join(parent_dir, name)
        if os.path.exists(path):
            QMessageBox.warning(self, "Explorer", "Bunday nom allaqachon bor.")
            return
        try:
            if folder:
                os.makedirs(path)
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                open(path, "w", encoding="utf-8").close()
        except OSError as e:
            QMessageBox.critical(self, "Explorer", str(e))
            return
        if not folder:
            self.file_opened.emit(os.path.normpath(path))

    def _rename(self, path):
        name, ok = QInputDialog.getText(self, "Rename", "Yangi nom:", text=os.path.basename(path))
        name = name.strip()
        if not ok or not name or name == os.path.basename(path):
            return
        new = os.path.join(os.path.dirname(path), name)
        if os.path.exists(new):
            QMessageBox.warning(self, "Rename", "Bunday nom allaqachon bor.")
            return
        try:
            os.rename(path, new)
        except OSError as e:
            QMessageBox.critical(self, "Rename", str(e))
            return
        self.path_renamed.emit(path, os.path.normpath(new))

    def _delete(self, path):
        answer = QMessageBox.question(
            self, "Delete", f"'{os.path.basename(path)}' o'chirilsinmi? Bu qaytarilmaydi.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
        except OSError as e:
            QMessageBox.critical(self, "Delete", str(e))
            return
        self.path_deleted.emit(path)

    def _reveal(self, path):
        if sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        else:
            subprocess.Popen(["xdg-open", path if os.path.isdir(path) else os.path.dirname(path)])
