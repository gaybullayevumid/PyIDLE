import os
import shutil

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core import runner
from core.syntax import LABELS
from editor.editor_widget import CodeEditor
from editor.file_explorer import FileExplorer
from editor.find_bar import FindBar
from editor.settings import SettingsDialog, settings
from editor.terminal import Terminal

THEME_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "themes")
MAX_SIZE = 5 * 1024 * 1024


def read_file(path):
    """(matn, qator oxiri). Binar yoki juda katta fayl uchun ValueError."""
    with open(path, "rb") as f:
        data = f.read(MAX_SIZE + 1)
    if len(data) > MAX_SIZE:
        raise ValueError("Fayl juda katta (5 MB dan oshiq).")
    if b"\x00" in data[:8192]:
        raise ValueError("Bu binar fayl, matn muharririda ochib bo'lmaydi.")
    text = data.decode("utf-8-sig")
    eol = "\r\n" if "\r\n" in text else "\n"
    return text.replace("\r\n", "\n"), eol


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyIDLE")
        self.resize(1200, 760)
        self.folder = None
        self._after_run = None

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._update_status)

        self.find_bar = FindBar(self.current_editor)
        central = QWidget()
        box = QVBoxLayout(central)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)
        box.addWidget(self.tabs, 1)
        box.addWidget(self.find_bar)
        self.setCentralWidget(central)

        self.explorer = FileExplorer(self)
        self.explorer.file_opened.connect(self.open_path)
        self.explorer.path_deleted.connect(self._on_path_deleted)
        self.explorer.path_renamed.connect(self._on_path_renamed)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.explorer)
        self.explorer.hide()

        self.terminal = Terminal(self)
        self.terminal.finished.connect(self._on_terminal_finished)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.terminal)
        self.terminal.hide()

        self.lbl_problems = QLabel("")
        self.lbl_pos = QLabel("")
        self.lbl_lang = QLabel("")
        for lbl in (self.lbl_problems, self.lbl_pos, self.lbl_lang):
            lbl.setContentsMargins(10, 0, 10, 0)
            self.statusBar().addPermanentWidget(lbl)

        self._build_menu()
        self._load_theme()
        self.statusBar().showMessage("Papka oching: File > Open Folder")

        last = settings.get("last_folder")
        if last and os.path.isdir(last):
            self._set_folder(last)

    # --- UI ---
    def _action(self, menu, text, slot, shortcut=None):
        act = QAction(text, self)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        act.triggered.connect(lambda _checked=False: slot())
        menu.addAction(act)
        return act

    def _build_menu(self):
        bar = self.menuBar()
        ed = lambda fn: (lambda: self._with_editor(fn))

        file_menu = bar.addMenu("File")
        self._action(file_menu, "New File", self.new_file, "Ctrl+N")
        projects = file_menu.addMenu("New Project")
        self._action(projects, "HTML / CSS / JS", lambda: self.new_project("html"))
        self._action(projects, "Django", lambda: self.new_project("django"))
        self._action(projects, "React (Vite)", lambda: self.new_project("react"))
        file_menu.addSeparator()
        self._action(file_menu, "Open File", self.open_file_dialog, "Ctrl+O")
        self._action(file_menu, "Open Folder", self.open_folder, "Ctrl+Shift+O")
        file_menu.addSeparator()
        self._action(file_menu, "Save", self.save, "Ctrl+S")
        self._action(file_menu, "Save As", self.save_as, "Ctrl+Shift+S")
        self._action(file_menu, "Save All", self.save_all, "Ctrl+Alt+S")
        file_menu.addSeparator()
        self._action(file_menu, "Settings", self.open_settings, "Ctrl+,")
        file_menu.addSeparator()
        self._action(file_menu, "Close Tab", lambda: self.close_tab(self.tabs.currentIndex()), "Ctrl+W")
        self._action(file_menu, "Exit", self.close, "Ctrl+Q")

        edit_menu = bar.addMenu("Edit")
        self._action(edit_menu, "Undo", ed(lambda e: e.undo()), "Ctrl+Z")
        self._action(edit_menu, "Redo", ed(lambda e: e.redo()), "Ctrl+Y")
        edit_menu.addSeparator()
        self._action(edit_menu, "Cut", ed(lambda e: e.cut()))
        self._action(edit_menu, "Copy", ed(lambda e: e.copy()))
        self._action(edit_menu, "Paste", ed(lambda e: e.paste()))
        edit_menu.addSeparator()
        self._action(edit_menu, "Find", lambda: self.find_bar.open(False), "Ctrl+F")
        self._action(edit_menu, "Replace", lambda: self.find_bar.open(True), "Ctrl+H")
        self._action(edit_menu, "Go to Line", self.go_to_line, "Ctrl+G")
        edit_menu.addSeparator()
        self._action(edit_menu, "Toggle Comment", ed(lambda e: e.toggle_comment()), "Ctrl+/")
        self._action(edit_menu, "Duplicate Line", ed(lambda e: e.duplicate_line()), "Ctrl+Shift+D")

        view_menu = bar.addMenu("View")
        self._action(view_menu, "Explorer", self.toggle_explorer, "Ctrl+B")
        self._action(view_menu, "Terminal", self.toggle_terminal, "Ctrl+`")
        view_menu.addSeparator()
        self._action(view_menu, "Zoom In", lambda: self.zoom(1), "Ctrl+=")
        self._action(view_menu, "Zoom Out", lambda: self.zoom(-1), "Ctrl+-")
        view_menu.addSeparator()
        self._action(view_menu, "Fullscreen", self.toggle_fullscreen, "F11")

        run_menu = bar.addMenu("Run")
        self._action(run_menu, "Run File", self.run_file, "F5")
        self._action(run_menu, "Stop", self.terminal.stop, "Shift+F5")
        self._action(run_menu, "Open in Browser", self.open_in_browser, "F6")
        run_menu.addSeparator()

        py_menu = run_menu.addMenu("Python")
        self._action(py_menu, "Create virtual environment (.venv)", self.create_venv)
        self._action(py_menu, "pip install -r requirements.txt", lambda: self.pip("-r requirements.txt"))
        self._action(py_menu, "pip install django", lambda: self.pip("django"))

        dj = run_menu.addMenu("Django")
        self._action(dj, "runserver", lambda: self.django("runserver"))
        self._action(dj, "makemigrations", lambda: self.django("makemigrations"))
        self._action(dj, "migrate", lambda: self.django("migrate"))
        self._action(dj, "collectstatic --noinput", lambda: self.django("collectstatic --noinput"))
        self._action(dj, "test", lambda: self.django("test"))
        self._action(dj, "startapp...", self.django_startapp)
        dj.addSeparator()
        self._action(dj, "createsuperuser (console)", lambda: self.django("createsuperuser", external=True))
        self._action(dj, "shell (console)", lambda: self.django("shell", external=True))

        self.npm_menu = run_menu.addMenu("npm / React")
        self.npm_menu.aboutToShow.connect(self._fill_npm_menu)

        term_menu = bar.addMenu("Terminal")
        self._action(term_menu, "New Command", self._focus_terminal, "Ctrl+Shift+`")
        self._action(term_menu, "Clear", self.terminal.clear)
        self._action(term_menu, "External Console", self.external_console)

        help_menu = bar.addMenu("Help")
        self._action(help_menu, "About", self.about)

    def _fill_npm_menu(self):
        menu = self.npm_menu
        menu.clear()
        self._action(menu, "npm install", lambda: self.npm("install"))
        scripts = runner.npm_scripts(self.folder)
        if scripts:
            menu.addSeparator()
        for name in scripts:
            self._action(menu, f"npm run {name}", lambda n=name: self.npm(f"run {n}"))

    def _load_theme(self):
        path = os.path.join(THEME_DIR, f"{settings.get('theme')}.qss")
        try:
            with open(path, encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except OSError:
            pass

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            dialog.save()
            self._load_theme()
            for i in range(self.tabs.count()):
                self.tabs.widget(i).apply_settings()

    def zoom(self, delta):
        editor = self.current_editor()
        if editor:
            editor.zoom(delta)
            for i in range(self.tabs.count()):
                if self.tabs.widget(i) is not editor:
                    self.tabs.widget(i).apply_settings()

    def about(self):
        QMessageBox.about(
            self, "PyIDLE",
            "PyIDLE — Python, Django, HTML, CSS, JavaScript va React uchun yengil kod muharriri.\n\n"
            "F5 — faylni ishga tushirish, Ctrl+` — terminal, Ctrl+B — explorer.",
        )

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
        editor.cursorPositionChanged.connect(lambda: self._update_status() if editor is self.current_editor() else None)
        editor.lint_changed.connect(lambda _p: self._update_status() if editor is self.current_editor() else None)
        editor.run_lint()
        editor.setFocus()
        return editor

    def _update_title(self, editor):
        index = self.tabs.indexOf(editor)
        if index < 0:
            return
        name = os.path.basename(editor.path) if editor.path else "untitled"
        self.tabs.setTabText(index, name + (" ●" if editor.document().isModified() else ""))

    def _update_status(self, *_):
        editor = self.current_editor()
        if not editor:
            self.lbl_pos.setText("")
            self.lbl_lang.setText("")
            self.lbl_problems.setText("")
            return
        cur = editor.textCursor()
        self.lbl_pos.setText(f"Ln {cur.blockNumber() + 1}, Col {cur.positionInBlock() + 1}")
        self.lbl_lang.setText(LABELS.get(editor.lang, editor.lang))
        if editor.problems:
            line, _col, msg = editor.problems[0]
            self.lbl_problems.setText(f"✖ {len(editor.problems)} xato — {line}-qator: {msg}")
        else:
            self.lbl_problems.setText("")

    def _info(self, text, error=False):
        if error:
            QMessageBox.warning(self, "PyIDLE", text)
        else:
            self.statusBar().showMessage(text, 5000)

    # --- fayl amallari ---
    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def toggle_explorer(self):
        if self.explorer.isVisible():
            self.explorer.hide()
        elif self.folder:
            self.explorer.show()
        else:
            self.open_folder()

    def toggle_terminal(self):
        if self.terminal.isVisible():
            self.terminal.hide()
        else:
            self.terminal.show()
            self.terminal.focus_input()

    def _focus_terminal(self):
        self.terminal.show()
        self.terminal.focus_input()

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", self.folder or "")
        if folder:
            self._set_folder(folder)

    def _set_folder(self, folder):
        folder = os.path.normpath(folder)
        self.folder = folder
        settings.set("last_folder", folder)
        self.explorer.set_root(folder)
        self.explorer.show()
        self.terminal.set_cwd(folder)
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
            text, eol = read_file(path)
        except (OSError, ValueError) as e:
            QMessageBox.critical(self, "Open File", f"Faylni ochib bo'lmadi:\n{e}")
            return
        editor = CodeEditor(path)
        editor.eol = eol
        editor.setPlainText(text)
        editor.document().setModified(False)
        self._add_tab(editor, os.path.basename(path))

    def save(self):
        editor = self.current_editor()
        if not editor:
            return False
        if not editor.path:
            return self.save_as()
        return self._write(editor, editor.path)

    def save_as(self):
        editor = self.current_editor()
        if not editor:
            return False
        path, _ = QFileDialog.getSaveFileName(self, "Save As", self.folder or "", "All files (*)")
        return bool(path) and self._write(editor, os.path.normpath(path))

    def save_all(self):
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if editor.document().isModified():
                if editor.path:
                    if not self._write(editor, editor.path):
                        return False
                else:
                    self.tabs.setCurrentIndex(i)
                    if not self.save_as():
                        return False
        return True

    def _write(self, editor, path):
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(editor.toPlainText().replace("\n", editor.eol))
        except OSError as e:
            QMessageBox.critical(self, "Save", str(e))
            return False
        editor.set_path(path)
        editor.document().setModified(False)
        self._update_title(editor)
        self._update_status()
        self.statusBar().showMessage(f"Saqlandi: {path}", 3000)
        return True

    def close_tab(self, index):
        if index < 0:
            return True
        editor = self.tabs.widget(index)
        if editor.document().isModified():
            name = os.path.basename(editor.path) if editor.path else "untitled"
            answer = QMessageBox.question(
                self, "Saqlash", f"'{name}' o'zgargan. Saqlansinmi?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if answer == QMessageBox.StandardButton.Cancel:
                return False
            if answer == QMessageBox.StandardButton.Save:
                self.tabs.setCurrentIndex(index)
                if not self.save():
                    return False
        self._remove_tab(index)
        return True

    def _remove_tab(self, index):
        editor = self.tabs.widget(index)
        self.tabs.removeTab(index)
        editor.deleteLater()

    def go_to_line(self):
        editor = self.current_editor()
        if not editor:
            return
        line, ok = QInputDialog.getInt(self, "Go to Line", "Qator raqami:", editor.textCursor().blockNumber() + 1, 1,
                                       editor.blockCount())
        if ok:
            editor.go_to_line(line)

    # --- explorer'dan kelgan o'zgarishlar ---
    def _under(self, path, base):
        return path == base or path.startswith(base + os.sep)

    def _on_path_deleted(self, path):
        for i in reversed(range(self.tabs.count())):
            editor = self.tabs.widget(i)
            if editor.path and self._under(editor.path, path):
                self._remove_tab(i)

    def _on_path_renamed(self, old, new):
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if editor.path and self._under(editor.path, old):
                editor.set_path(new + editor.path[len(old):])
                self._update_title(editor)
        self._update_status()

    # --- ishga tushirish ---
    def _run_shell(self, cmdline, cwd, after=None):
        self.terminal.show()
        if self.terminal.run(cmdline, cwd):
            self._after_run = after

    def _on_terminal_finished(self, code):
        after, self._after_run = self._after_run, None
        if after and code == 0:
            after()

    def run_file(self):
        editor = self.current_editor()
        if not editor:
            self._info("Ishga tushirish uchun fayl oching.")
            return
        if self.terminal.is_running():
            self._info("Avval joriy jarayonni to'xtating (Shift+F5).", error=True)
            return
        if not self.save_all():
            return
        if not editor.path:
            return
        result = runner.command_for_file(editor.path, self.folder)
        if result[0] == "browser":
            runner.open_in_browser(result[1])
        elif result[0] == "shell":
            self._run_shell(result[1], result[2])
        else:
            self._info(result[1], error=True)

    def open_in_browser(self):
        editor = self.current_editor()
        if not editor or not editor.path or not editor.path.lower().endswith((".html", ".htm")):
            self._info("Brauzerda ochish uchun HTML faylni oching.", error=True)
            return
        self.save_all()
        runner.open_in_browser(editor.path)

    def _python(self):
        py = runner.python_exe(self.folder)
        if not py:
            self._info("Python topilmadi. Python'ni o'rnating yoki PATH ga qo'shing.", error=True)
        return py

    def pip(self, args):
        py = self._python()
        if py:
            self._run_shell(f"{runner.q(py)} -m pip install {args}", self.folder)

    def create_venv(self):
        if not self.folder:
            self._info("Avval papka oching.", error=True)
            return
        py = self._python()
        if py:
            self._run_shell(f"{runner.q(py)} -m venv .venv", self.folder)

    def django(self, args, external=False):
        root = runner.django_dir(self.folder)
        py = self._python()
        if not py:
            return
        if not root:
            self._info("manage.py topilmadi. Django loyihasi papkasini oching.", error=True)
            return
        cmd = f"{runner.q(py)} manage.py {args}"
        if external:
            if not runner.launch_external(cmd, root):
                self._info("Konsol oynasini ochib bo'lmadi.", error=True)
        else:
            self._run_shell(cmd, root)

    def django_startapp(self):
        name, ok = QInputDialog.getText(self, "startapp", "Ilova nomi:")
        name = name.strip()
        if ok and name.isidentifier():
            self.django(f"startapp {name}")
        elif ok:
            self._info("Ilova nomi faqat harf, raqam va _ dan iborat bo'lishi kerak.", error=True)

    def npm(self, args):
        if not self.folder or not os.path.isfile(os.path.join(self.folder, "package.json")) and args != "install":
            self._info("package.json topilmadi. React loyihasi papkasini oching.", error=True)
            return
        if not shutil.which("npm"):
            self._info("npm topilmadi. Node.js ni https://nodejs.org dan o'rnating.", error=True)
            return
        self._run_shell(f"npm {args}", self.folder)

    def external_console(self):
        if not runner.launch_external("", self.terminal.cwd):
            self._info("Konsol oynasini ochib bo'lmadi.", error=True)

    # --- yangi loyiha ---
    def new_project(self, kind):
        name, ok = QInputDialog.getText(self, "New Project", "Loyiha nomi:", text="myproject")
        name = name.strip()
        if not ok or not name:
            return
        if not name.replace("_", "").replace("-", "").isalnum() or (kind == "django" and not name.isidentifier()):
            self._info("Nom noto'g'ri (Django uchun faqat harf, raqam va _; raqamdan boshlanmasin).", error=True)
            return
        parent = QFileDialog.getExistingDirectory(self, "Loyiha qayerda yaratilsin?", self.folder or "")
        if not parent:
            return
        root = os.path.join(parent, name)
        if os.path.exists(root) and os.listdir(root):
            self._info("Bu nomdagi papka allaqachon mavjud va bo'sh emas.", error=True)
            return

        if kind == "html":
            try:
                runner.create_html_project(parent, name)
            except OSError as e:
                self._info(str(e), error=True)
                return
            self._set_folder(root)
            self.open_path(os.path.join(root, "index.html"))
            return

        def opened():
            if os.path.isdir(root):
                self._set_folder(root)

        if kind == "django":
            py = self._python()
            if py:
                self._run_shell(runner.django_new_project(parent, name), parent, after=opened)
        else:
            if not shutil.which("npm"):
                self._info("npm topilmadi. Node.js ni https://nodejs.org dan o'rnating.", error=True)
                return
            self._run_shell(runner.react_new_project(name), parent, after=opened)

    def closeEvent(self, event):
        if self.terminal.is_running():
            self.terminal.stop()
        while self.tabs.count():
            self.tabs.setCurrentIndex(0)
            if not self.close_tab(0):
                event.ignore()
                return
        event.accept()
