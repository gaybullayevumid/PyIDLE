import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QTabWidget,
)

from editor.editor_widget import CodeEditor
from editor.file_explorer import FileExplorer

THEME = os.path.join(os.path.dirname(os.path.dirname(__file__)), "themes", "dark.qss")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyIDLE")
        self.resize(1100, 700)
        self.folder = None

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self.explorer = FileExplorer(self)
        self.explorer.file_opened.connect(self.open_path)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.explorer)
        self.explorer.hide()

        self._build_menu()
        self._load_theme()
        self.statusBar().showMessage("Papka oching: File > Open Folder")

    # --- UI ---
    def _action(self, menu, text, slot, shortcut=None):
        act = QAction(text, self)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        act.triggered.connect(slot)
        menu.addAction(act)
        return act

    def _build_menu(self):
        bar = self.menuBar()

        file_menu = bar.addMenu("File")
        self._action(file_menu, "New File", self.new_file, "Ctrl+N")
        file_menu.addSeparator()
        self._action(file_menu, "Open File", self.open_file_dialog, "Ctrl+O")
        self._action(file_menu, "Open Folder", self.open_folder, "Ctrl+Shift+O")
        file_menu.addSeparator()
        self._action(file_menu, "Save", self.save, "Ctrl+S")
        self._action(file_menu, "Save As", self.save_as, "Ctrl+Shift+S")
        file_menu.addSeparator()
        self._action(file_menu, "Exit", self.close, "Ctrl+Q")

        edit_menu = bar.addMenu("Edit")
        self._action(edit_menu, "Undo", lambda: self._with_editor(lambda e: e.undo()), "Ctrl+Z")
        self._action(edit_menu, "Redo", lambda: self._with_editor(lambda e: e.redo()), "Ctrl+Y")

        view_menu = bar.addMenu("View")
        self._action(view_menu, "Fullscreen", self.toggle_fullscreen, "F11")

    def _load_theme(self):
        try:
            with open(THEME, encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except OSError:
            pass

    # --- helpers ---
    def current_editor(self):
        return self.tabs.currentWidget()

    def _with_editor(self, fn):
        editor = self.current_editor()
        if editor:
            fn(editor)

    def _add_tab(self, editor, title):
        index = self.tabs.addTab(editor, title)
        self.tabs.setCurrentIndex(index)
        editor.document().modificationChanged.connect(lambda _: self._update_title(editor))
        editor.setFocus()
        return editor

    def _update_title(self, editor):
        index = self.tabs.indexOf(editor)
        if index < 0:
            return
        name = os.path.basename(editor.path) if editor.path else "untitled"
        self.tabs.setTabText(index, name + (" ●" if editor.document().isModified() else ""))

    # --- file actions ---
    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", self.folder or "")
        if folder:
            self.folder = folder
            self.explorer.set_root(folder)
            self.explorer.show()
            self.setWindowTitle(f"PyIDLE - {os.path.basename(folder)}")
            self.statusBar().showMessage(folder)

    def new_file(self):
        if not self.folder:
            self._add_tab(CodeEditor(), "untitled")
            return
        name, ok = QInputDialog.getText(self, "New File", "Fayl nomi:", text="main.py")
        name = name.strip()
        if not ok or not name:
            return
        path = os.path.join(self.folder, name)
        if os.path.exists(path):
            QMessageBox.warning(self, "New File", "Bunday fayl allaqachon bor.")
            return
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "w", encoding="utf-8").close()
        except OSError as e:
            QMessageBox.critical(self, "New File", str(e))
            return
        self.open_path(path)

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", self.folder or "")
        if path:
            self.open_path(path)

    def open_path(self, path):
        path = os.path.normpath(path)
        for i in range(self.tabs.count()):
            if self.tabs.widget(i).path == path:
                self.tabs.setCurrentIndex(i)
                return
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError) as e:
            QMessageBox.critical(self, "Open File", f"Faylni ochib bo'lmadi:\n{e}")
            return
        editor = CodeEditor(path)
        editor.setPlainText(text)
        self._add_tab(editor, os.path.basename(path))

    def save(self):
        editor = self.current_editor()
        if not editor:
            return
        if not editor.path:
            return self.save_as()
        self._write(editor, editor.path)

    def save_as(self):
        editor = self.current_editor()
        if not editor:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save As", self.folder or "", "Python (*.py);;All files (*)")
        if path:
            self._write(editor, os.path.normpath(path))

    def _write(self, editor, path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())
        except OSError as e:
            QMessageBox.critical(self, "Save", str(e))
            return False
        editor.path = path
        editor.document().setModified(False)
        self._update_title(editor)
        self.statusBar().showMessage(f"Saqlandi: {path}", 3000)
        return True

    def close_tab(self, index):
        editor = self.tabs.widget(index)
        if editor.document().isModified():
            name = os.path.basename(editor.path) if editor.path else "untitled"
            answer = QMessageBox.question(
                self, "Saqlash", f"'{name}' o'zgargan. Saqlansinmi?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if answer == QMessageBox.StandardButton.Cancel:
                return
            if answer == QMessageBox.StandardButton.Save and not self._write_or_ask(editor):
                return
        self.tabs.removeTab(index)
        editor.deleteLater()

    def _write_or_ask(self, editor):
        if editor.path:
            return self._write(editor, editor.path)
        path, _ = QFileDialog.getSaveFileName(self, "Save As", self.folder or "")
        return bool(path) and self._write(editor, os.path.normpath(path))

    def closeEvent(self, event):
        while self.tabs.count():
            before = self.tabs.count()
            self.tabs.setCurrentIndex(0)
            self.close_tab(0)
            if self.tabs.count() == before:
                event.ignore()
                return
        event.accept()
