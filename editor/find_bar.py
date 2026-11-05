from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument
from PyQt6.QtWidgets import QCheckBox, QGridLayout, QLineEdit, QPushButton, QWidget


class FindBar(QWidget):
    """Ctrl+F — qidirish, Ctrl+H — almashtirish."""

    def __init__(self, get_editor, parent=None):
        super().__init__(parent)
        self.setObjectName("findBar")
        self.get_editor = get_editor

        self.find = QLineEdit()
        self.find.setPlaceholderText("Find")
        self.replace = QLineEdit()
        self.replace.setPlaceholderText("Replace")
        self.case = QCheckBox("Aa")
        self.case.setToolTip("Katta-kichik harf farqi")

        grid = QGridLayout(self)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.addWidget(self.find, 0, 0)
        grid.addWidget(self.case, 0, 1)
        for col, (text, slot) in enumerate((("Prev", self.prev), ("Next", self.next), ("Close", self.hide)), start=2):
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            grid.addWidget(btn, 0, col)
        grid.addWidget(self.replace, 1, 0)
        self.btn_replace = QPushButton("Replace")
        self.btn_replace.clicked.connect(self.replace_one)
        self.btn_all = QPushButton("All")
        self.btn_all.clicked.connect(self.replace_all)
        grid.addWidget(self.btn_replace, 1, 2)
        grid.addWidget(self.btn_all, 1, 3)
        self.replace_widgets = (self.replace, self.btn_replace, self.btn_all)

        self.find.returnPressed.connect(self.next)
        self.find.textChanged.connect(lambda: self.next(from_start=True))
        self.hide()

    def open(self, replace=False):
        editor = self.get_editor()
        if editor and editor.textCursor().hasSelection():
            self.find.setText(editor.textCursor().selectedText())
        for w in self.replace_widgets:
            w.setVisible(replace)
        self.show()
        self.find.setFocus()
        self.find.selectAll()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            editor = self.get_editor()
            if editor:
                editor.setFocus()
            return
        super().keyPressEvent(event)

    def _flags(self, backward=False):
        flags = QTextDocument.FindFlag(0)
        if self.case.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward
        return flags

    def _search(self, backward=False, from_start=False):
        editor = self.get_editor()
        text = self.find.text()
        if not editor or not text:
            return False
        cur = editor.textCursor()
        if from_start:
            cur.setPosition(cur.selectionStart())
        found = editor.document().find(text, cur, self._flags(backward))
        if found.isNull():  # boshidan/oxiridan davom etish
            wrap = editor.textCursor()
            wrap.movePosition(wrap.MoveOperation.End if backward else wrap.MoveOperation.Start)
            found = editor.document().find(text, wrap, self._flags(backward))
        if found.isNull():
            return False
        editor.setTextCursor(found)
        editor.centerCursor()
        return True

    def next(self, from_start=False):
        self._search(False, from_start is True)

    def prev(self):
        self._search(True)

    def replace_one(self):
        editor = self.get_editor()
        if not editor:
            return
        cur = editor.textCursor()
        sel = cur.selectedText()
        match = sel == self.find.text() if self.case.isChecked() else sel.lower() == self.find.text().lower()
        if cur.hasSelection() and match:
            cur.insertText(self.replace.text())
        self._search()

    def replace_all(self):
        editor = self.get_editor()
        text = self.find.text()
        if not editor or not text:
            return
        doc = editor.document()
        cur = editor.textCursor()
        cur.beginEditBlock()
        pos = cur.document().find(text, 0, self._flags())
        while not pos.isNull():
            pos.insertText(self.replace.text())
            pos = doc.find(text, pos, self._flags())
        cur.endEditBlock()
