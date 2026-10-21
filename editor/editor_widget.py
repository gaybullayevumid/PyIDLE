from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QTextFormat
from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from core.syntax import PythonHighlighter


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    TAB = "    "

    def __init__(self, path=None):
        super().__init__()
        self.path = path
        self.setFont(QFont("Consolas", 11))
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.highlighter = PythonHighlighter(self.document())

        self.line_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_margin)
        self.updateRequest.connect(self.update_line_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_margin()
        self.highlight_current_line()

    # --- qator raqamlari ---
    def line_number_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 20 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_margin(self):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def update_line_area(self, rect, dy):
        if dy:
            self.line_area.scroll(0, dy)
        else:
            self.line_area.update(0, rect.y(), self.line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_margin()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_width(), cr.height()))

    def paint_line_numbers(self, event):
        painter = QPainter(self.line_area)
        painter.fillRect(event.rect(), QColor("#181818"))
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        current = self.textCursor().blockNumber()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor("#CCCCCC" if number == current else "#5A5A5A"))
                painter.drawText(
                    0, top, self.line_area.width() - 8, self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, str(number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            number += 1

    def highlight_current_line(self):
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor("#222222"))
        sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        sel.cursor = self.textCursor()
        sel.cursor.clearSelection()
        self.setExtraSelections([sel])
        self.line_area.update()

    # --- Tab / auto-indent ---
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab:
            self.insertPlainText(self.TAB)
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            line = self.textCursor().block().text()
            indent = line[: len(line) - len(line.lstrip(" "))]
            if line.rstrip().endswith(":"):
                indent += self.TAB
            super().keyPressEvent(event)
            self.insertPlainText(indent)
            return
        super().keyPressEvent(event)
