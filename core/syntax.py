import keyword

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


def _fmt(color, bold=False, italic=False):
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Weight.Bold)
    f.setFontItalic(italic)
    return f


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        kw = "|".join(keyword.kwlist)
        self.rules = [
            (QRegularExpression(r"\b(" + kw + r")\b"), _fmt("#C586C0")),
            (QRegularExpression(r"\b(self|cls|True|False|None)\b"), _fmt("#569CD6")),
            (QRegularExpression(r"\b(def|class)\s+(\w+)"), _fmt("#DCDCAA")),
            (QRegularExpression(r"\b\d+(\.\d+)?\b"), _fmt("#B5CEA8")),
            (QRegularExpression(r"\"[^\"\\\n]*(\\.[^\"\\\n]*)*\"|'[^'\\\n]*(\\.[^'\\\n]*)*'"), _fmt("#CE9178")),
            (QRegularExpression(r"#[^\n]*"), _fmt("#6A9955", italic=True)),
        ]
        self.def_name = _fmt("#DCDCAA")
        self.kw_fmt = self.rules[0][1]

    def highlightBlock(self, text):
        for regex, fmt in self.rules:
            it = regex.globalMatch(text)
            while it.hasNext():
                m = it.next()
                if regex.pattern().startswith(r"\b(def|class)"):
                    # keyword rangi + nom rangi
                    self.setFormat(m.capturedStart(2), m.capturedLength(2), self.def_name)
                else:
                    self.setFormat(m.capturedStart(), m.capturedLength(), fmt)
