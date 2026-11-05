import re

from PyQt6.QtCore import QRect, QSize, QStringListModel, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QTextCharFormat, QTextCursor, QTextFormat
from PyQt6.QtWidgets import QCompleter, QPlainTextEdit, QTextEdit, QWidget

from core.autocomplete import completions
from core.linter import lint
from core.syntax import COMMENT_SYNTAX, INDENT_WIDTH, PALETTES, CodeHighlighter, language_for
from editor.settings import settings

PAIRS = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'", "`": "`"}
CLOSERS = set(PAIRS.values())
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
OPEN_TAG = re.compile(r"<([A-Za-z][\w.:-]*)(?:\s[^<>]*)?>$")


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    lint_changed = pyqtSignal(list)

    def __init__(self, path=None):
        super().__init__()
        self.path = path
        self.eol = "\n"
        self.problems = []
        self.lang = language_for(path)
        self.palette_ = PALETTES[settings.get("theme")]

        self.highlighter = CodeHighlighter(self.document(), self.lang, settings.get("theme"))

        self.line_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_margin)
        self.updateRequest.connect(self.update_line_area)
        self.cursorPositionChanged.connect(self.refresh_selections)

        self.completer = QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setModel(QStringListModel(self.completer))
        self.completer.activated[str].connect(self.insert_completion)

        self.lint_timer = QTimer(self)
        self.lint_timer.setSingleShot(True)
        self.lint_timer.setInterval(500)
        self.lint_timer.timeout.connect(self.run_lint)
        self.textChanged.connect(self.lint_timer.start)

        self.apply_settings()

    # --- sozlamalar / til ---
    @property
    def indent(self):
        return " " * INDENT_WIDTH[self.lang]

    def apply_settings(self):
        theme = settings.get("theme")
        self.palette_ = PALETTES[theme]
        self.setFont(QFont(settings.get("font_family"), settings.get("font_size")))
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * INDENT_WIDTH[self.lang])
        self.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.WidgetWidth if settings.get("word_wrap") else QPlainTextEdit.LineWrapMode.NoWrap
        )
        self.highlighter.set_theme(theme)
        self.update_margin()
        self.refresh_selections()

    def set_path(self, path):
        self.path = path
        lang = language_for(path)
        if lang != self.lang:
            self.lang = lang
            self.highlighter.set_language(lang)
            self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * INDENT_WIDTH[lang])
            self.run_lint()

    def zoom(self, delta):
        size = max(6, min(40, settings.get("font_size") + delta))
        settings.set("font_size", size)
        self.apply_settings()

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
        pal = self.palette_
        painter = QPainter(self.line_area)
        painter.fillRect(event.rect(), QColor(pal["gutter_bg"]))
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        current = self.textCursor().blockNumber()
        bad = {p[0] - 1 for p in self.problems}
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                color = pal["error"] if number in bad else pal["gutter_cur"] if number == current else pal["gutter_fg"]
                painter.setPen(QColor(color))
                painter.drawText(
                    0, top, self.line_area.width() - 8, self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, str(number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            number += 1

    # --- joriy qator va xatolar ---
    def refresh_selections(self):
        sels = []
        cur = QTextEdit.ExtraSelection()
        cur.format.setBackground(QColor(self.palette_["line_bg"]))
        cur.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        cur.cursor = self.textCursor()
        cur.cursor.clearSelection()
        sels.append(cur)

        doc = self.document()
        for line, col, _msg in self.problems:
            block = doc.findBlockByNumber(line - 1)
            if not block.isValid():
                continue
            sel = QTextEdit.ExtraSelection()
            fmt = QTextCharFormat()
            fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
            fmt.setUnderlineColor(QColor(self.palette_["error"]))
            sel.format = fmt
            c = QTextCursor(block)
            start = min(col, max(0, block.length() - 1))
            c.setPosition(block.position() + start)
            c.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
            if not c.hasSelection():
                c.setPosition(block.position())
                c.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
            sel.cursor = c
            sels.append(sel)
        self.setExtraSelections(sels)
        self.line_area.update()

    def run_lint(self):
        self.problems = lint(self.lang, self.toPlainText())
        self.refresh_selections()
        self.lint_changed.emit(self.problems)

    # --- avtotoldirish ---
    def _prefix(self):
        before = self.textCursor().block().text()[: self.textCursor().positionInBlock()]
        pattern = r"[\w$-]*$" if self.lang in ("css", "html") else r"[\w$]*$"
        return re.search(pattern, before).group(0)

    def insert_completion(self, text):
        prefix = self._prefix()
        cur = self.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, len(prefix))
        cur.insertText(text)
        self.setTextCursor(cur)

    def _show_completions(self):
        prefix = self._prefix()
        popup = self.completer.popup()
        if len(prefix) < 2:
            popup.hide()
            return
        self.completer.model().setStringList(completions(self.lang, self.toPlainText()))
        self.completer.setCompletionPrefix(prefix)
        if self.completer.completionCount() == 0 or (
            self.completer.completionCount() == 1 and self.completer.currentCompletion() == prefix
        ):
            popup.hide()
            return
        popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
        rect = self.cursorRect()
        rect.moveLeft(rect.left() + self.line_number_width())
        rect.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width() + 8)
        self.completer.complete(rect)

    # --- tahrirlash yordamchilari ---
    def _char_after(self):
        cur = self.textCursor()
        text = cur.block().text()
        i = cur.positionInBlock()
        return text[i] if i < len(text) else ""

    def _char_before(self):
        cur = self.textCursor()
        text = cur.block().text()
        i = cur.positionInBlock()
        return text[i - 1] if i > 0 else ""

    def _selected_blocks(self):
        cur = self.textCursor()
        doc = self.document()
        start = doc.findBlock(cur.selectionStart())
        end = doc.findBlock(cur.selectionEnd())
        if cur.hasSelection() and cur.selectionEnd() == end.position() and end != start:
            end = end.previous()
        return start.blockNumber(), end.blockNumber()

    def _edit_lines(self, fn):
        first, last = self._selected_blocks()
        cur = self.textCursor()
        cur.beginEditBlock()
        for n in range(first, last + 1):
            block = self.document().findBlockByNumber(n)
            c = QTextCursor(block)
            fn(c, block.text())
        cur.endEditBlock()

    def indent_selection(self):
        ind = self.indent
        self._edit_lines(lambda c, t: c.insertText(ind) if t.strip() else None)

    def unindent_selection(self):
        width = len(self.indent)

        def fn(c, text):
            n = min(width, len(text) - len(text.lstrip(" ")))
            if n:
                c.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, n)
                c.removeSelectedText()

        self._edit_lines(fn)

    def toggle_comment(self):
        syntax = COMMENT_SYNTAX.get(self.lang)
        if not syntax:
            return
        op, cl = syntax
        op_s, cl_s = op.strip(), cl.strip()
        first, last = self._selected_blocks()
        blocks = [self.document().findBlockByNumber(n) for n in range(first, last + 1)]
        lines = [b.text() for b in blocks if b.text().strip()]
        commented = bool(lines) and all(
            l.strip().startswith(op_s) and (not cl_s or l.rstrip().endswith(cl_s)) for l in lines
        )

        def fn(c, text):
            if not text.strip():
                return
            lead = len(text) - len(text.lstrip())
            c.setPosition(c.block().position() + lead)
            if commented:
                body = text[lead:]
                new = body[len(op_s):]
                if new.startswith(" "):
                    new = new[1:]
                if cl_s:
                    new = new.rstrip()
                    new = new[: -len(cl_s)].rstrip() if new.endswith(cl_s) else new
                c.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                c.insertText(new)
            else:
                c.insertText(op)
                if cl:
                    c.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                    c.insertText(cl)

        self._edit_lines(fn)

    def duplicate_line(self):
        cur = self.textCursor()
        cur.beginEditBlock()
        text = cur.selectedText().replace(" ", "\n") if cur.hasSelection() else None
        if text is not None:
            end = cur.selectionEnd()
            cur.setPosition(end)
            cur.insertText(text)
        else:
            line = cur.block().text()
            cur.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            cur.insertText("\n" + line)
        cur.endEditBlock()
        self.setTextCursor(cur)

    def go_to_line(self, line):
        block = self.document().findBlockByNumber(max(0, line - 1))
        if block.isValid():
            cur = QTextCursor(block)
            self.setTextCursor(cur)
            self.centerCursor()

    # --- klaviatura ---
    def keyPressEvent(self, event):
        key = event.key()
        popup = self.completer.popup()
        if popup.isVisible():
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
                text = self.completer.currentCompletion()
                popup.hide()
                if text:
                    self.insert_completion(text)
                return
            if key == Qt.Key.Key_Escape:
                popup.hide()
                return

        mods = event.modifiers()
        ctrl = bool(mods & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier))
        text = event.text()

        if key == Qt.Key.Key_Tab and not ctrl:
            if self.textCursor().hasSelection():
                self.indent_selection()
            else:
                self.insertPlainText(self.indent)
            return
        if key == Qt.Key.Key_Backtab:
            self.unindent_selection()
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not ctrl:
            self._newline()
            return
        if key == Qt.Key.Key_Backspace and not ctrl and not self.textCursor().hasSelection():
            before, after = self._char_before(), self._char_after()
            if before in PAIRS and PAIRS[before] == after:
                cur = self.textCursor()
                cur.beginEditBlock()
                cur.deleteChar()
                cur.deletePreviousChar()
                cur.endEditBlock()
                return
        if text and not ctrl and len(text) == 1 and self._pair_typed(text):
            return

        super().keyPressEvent(event)

        if text and not ctrl and len(text) == 1:
            if text == ">" and self.lang in ("html", "javascript"):
                self._close_tag()
            if text.isalnum() or text in "_$-":
                self._show_completions()
            else:
                popup.hide()

    def _newline(self):
        cur = self.textCursor()
        line = cur.block().text()
        before = line[: cur.positionInBlock()]
        after = line[cur.positionInBlock():]
        indent = line[: len(line) - len(line.lstrip(" \t"))]
        extra = ""
        stripped = before.rstrip()
        if self.lang == "python":
            if stripped.endswith(":"):
                extra = self.indent
        elif stripped and stripped[-1] in "{[(":
            extra = self.indent
        elif self.lang in ("html", "javascript") and OPEN_TAG.search(stripped):
            m = OPEN_TAG.search(stripped)
            if m.group(1).lower() not in VOID_TAGS and not stripped.endswith("/>"):
                extra = self.indent

        cur.beginEditBlock()
        cur.insertText("\n" + indent + extra)
        rest = after.lstrip()
        if extra and (rest[:1] in CLOSERS or rest.startswith("</")):
            pos = cur.position()
            cur.insertText("\n" + indent)
            cur.setPosition(pos)
        cur.endEditBlock()
        self.setTextCursor(cur)
        self.ensureCursorVisible()

    def _pair_typed(self, ch):
        cur = self.textCursor()
        after = self._char_after()
        before = self._char_before()
        if ch in CLOSERS and after == ch and not cur.hasSelection() and (ch not in "\"'`" or before != "\\"):
            cur.movePosition(QTextCursor.MoveOperation.Right)
            self.setTextCursor(cur)
            return True
        if ch not in PAIRS:
            return False
        if cur.hasSelection():
            sel = cur.selectedText()
            cur.insertText(ch + sel + PAIRS[ch])
            return True
        if ch in "\"'`":
            if before.isalnum() or before in ("\\", "_") or after.isalnum():
                return False
            if self.lang == "python" and ch == "'" and before == "'":
                return False
        elif after and not after.isspace() and after not in CLOSERS:
            return False
        cur.insertText(ch + PAIRS[ch])
        cur.movePosition(QTextCursor.MoveOperation.Left)
        self.setTextCursor(cur)
        return True

    def _close_tag(self):
        """<div> yozilganda </div> ni avtomatik qo'shish."""
        cur = self.textCursor()
        before = cur.block().text()[: cur.positionInBlock()]
        m = OPEN_TAG.search(before)
        if not m or before.endswith("/>"):
            return
        name = m.group(1)
        prev = before[m.start() - 1] if m.start() > 0 else ""
        if name.lower() in VOID_TAGS or prev.isalnum() or (prev != "" and prev in "_)]"):
            return
        cur.insertText(f"</{name}>")
        cur.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(name) + 3)
        self.setTextCursor(cur)
