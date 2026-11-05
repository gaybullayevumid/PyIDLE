import builtins
import keyword
import os
import re

from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

# --- til aniqlash ---------------------------------------------------------

EXTENSIONS = {
    ".py": "python", ".pyw": "python", ".pyi": "python",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".jsx": "javascript", ".ts": "javascript", ".tsx": "javascript",
    ".html": "html", ".htm": "html", ".jinja": "html", ".j2": "html", ".djhtml": "html",
    ".css": "css", ".scss": "css", ".less": "css",
    ".json": "json",
    ".md": "markdown", ".markdown": "markdown",
}

LABELS = {
    "python": "Python", "javascript": "JavaScript / React", "html": "HTML",
    "css": "CSS", "json": "JSON", "markdown": "Markdown", "text": "Text",
}

INDENT_WIDTH = {"python": 4, "javascript": 2, "html": 2, "css": 2, "json": 2, "markdown": 2, "text": 4}

# (ochuvchi, yopuvchi) — yopuvchi bo'sh bo'lsa qator izohi
COMMENT_SYNTAX = {
    "python": ("# ", ""), "javascript": ("// ", ""), "html": ("<!-- ", " -->"),
    "css": ("/* ", " */"), "json": None, "markdown": ("<!-- ", " -->"), "text": ("# ", ""),
}


def language_for(path):
    if not path:
        return "python"
    return EXTENSIONS.get(os.path.splitext(path)[1].lower(), "text")


# --- ranglar --------------------------------------------------------------

PALETTES = {
    "dark": {
        "bg": "#1E1E1E", "fg": "#D4D4D4", "gutter_bg": "#181818", "gutter_fg": "#5A5A5A",
        "gutter_cur": "#CCCCCC", "line_bg": "#222222", "error": "#F14C4C",
        "keyword": "#C586C0", "builtin": "#4EC9B0", "function": "#DCDCAA", "number": "#B5CEA8",
        "string": "#CE9178", "comment": "#6A9955", "tag": "#569CD6", "attr": "#9CDCFE",
        "decorator": "#DCDCAA", "special": "#569CD6", "type": "#4EC9B0", "template": "#D7BA7D",
        "punct": "#808080",
    },
    "light": {
        "bg": "#FFFFFF", "fg": "#1F1F1F", "gutter_bg": "#F3F3F3", "gutter_fg": "#999999",
        "gutter_cur": "#1F1F1F", "line_bg": "#F0F0F0", "error": "#E51400",
        "keyword": "#AF00DB", "builtin": "#267F99", "function": "#795E26", "number": "#098658",
        "string": "#A31515", "comment": "#008000", "tag": "#800000", "attr": "#E50000",
        "decorator": "#795E26", "special": "#0000FF", "type": "#267F99", "template": "#811F3F",
        "punct": "#800000",
    },
}

TOKEN_KEYS = (
    "keyword", "builtin", "function", "number", "string", "comment", "tag", "attr",
    "decorator", "special", "type", "template", "punct",
)


def _fmt(color, italic=False):
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    f.setFontItalic(italic)
    return f


# --- qoidalar -------------------------------------------------------------

def _r(pattern, key, group=0, flags=0):
    return re.compile(pattern, flags), {group: key}


def _words(words):
    return r"\b(?:" + "|".join(sorted(words, key=len, reverse=True)) + r")\b"


class _ML:
    """Ko'p qatorli blok (izoh, uch qo'shtirnoq, <script> ...)."""

    def __init__(self, start, end, key=None, inner=None):
        self.start, self.end = start, re.compile(end)
        self.key, self.inner = key, inner


class Language:
    def __init__(self, rules, ml=(), skip=None):
        self.rules = rules
        self.ml = list(ml)
        parts = [f"(?P<ml{i}>{m.start})" for i, m in enumerate(self.ml)]
        if skip:
            parts.append(f"(?P<skip>{skip})")
        self.scan = re.compile("|".join(parts)) if parts else None


_STR_DQ = r'"(?:[^"\\\n]|\\.)*"?'
_STR_SQ = r"'(?:[^'\\\n]|\\.)*'?"
_NUM = r"\b(?:0[xX][0-9a-fA-F_]+|\d[\d_]*\.?\d*(?:[eE][+-]?\d+)?j?)\b"


def _python():
    kw = [k for k in keyword.kwlist if k not in ("True", "False", "None")]
    bi = [n for n in dir(builtins) if not n.startswith("_") and not n[0].isupper()]
    skip = rf"[rRbBuUfF]{{0,2}}(?:{_STR_DQ}|{_STR_SQ})|#.*$"
    rules = [
        _r(r"\b([A-Za-z_]\w*)(?=\s*\()", "function", 1),
        _r(r"\b[A-Z][A-Za-z0-9_]*[a-z][A-Za-z0-9_]*\b", "type"),
        _r(_words(bi), "builtin"),
        _r(_words(kw), "keyword"),
        _r(r"\b(?:self|cls|True|False|None)\b", "special"),
        _r(r"\bdef\s+(\w+)", "function", 1),
        _r(r"\bclass\s+(\w+)", "type", 1),
        _r(r"^\s*(@[\w.]+)", "decorator", 1),
        _r(_NUM, "number"),
        (re.compile(rf"(?P<s>[rRbBuUfF]{{0,2}}(?:{_STR_DQ}|{_STR_SQ}))|(?P<c>#.*$)"),
         {"s": "string", "c": "comment"}),
    ]
    ml = [
        _ML(r'(?<!\w)[rRbBuUfF]{0,2}"""', r'"""', "string"),
        _ML(r"(?<!\w)[rRbBuUfF]{0,2}'''", r"'''", "string"),
    ]
    return Language(rules, ml, skip)


_JS_KEYWORDS = """break case catch class const continue debugger default delete do else export extends
finally for function if import in instanceof let new return super switch throw try typeof var void
while with yield async await of static get set from as interface type enum implements namespace declare
readonly public private protected abstract""".split()
_JS_BUILTINS = """console document window Math JSON Promise Array Object String Number Boolean Map Set
WeakMap Date RegExp Error fetch require module exports process localStorage sessionStorage setTimeout
setInterval clearTimeout clearInterval parseInt parseFloat isNaN useState useEffect useRef useMemo
useCallback useContext useReducer useLayoutEffect useNavigate useParams""".split()


def _javascript():
    skip = rf"{_STR_DQ}|{_STR_SQ}|//.*$"
    rules = [
        _r(r"\b([A-Za-z_$][\w$]*)(?=\s*\()", "function", 1),
        _r(r"\b[A-Z][A-Za-z0-9]*[a-z][A-Za-z0-9]*\b", "type"),
        _r(_words(_JS_BUILTINS), "builtin"),
        _r(_words(_JS_KEYWORDS), "keyword"),
        _r(r"\b(?:this|true|false|null|undefined|NaN|Infinity)\b", "special"),
        _r(r"\bfunction\s*\*?\s*([A-Za-z_$][\w$]*)", "function", 1),
        _r(r"\bclass\s+([A-Za-z_$][\w$]*)", "type", 1),
        _r(_NUM, "number"),
        # JSX
        _r(r"(?<![\w)\]<])</?([A-Za-z][\w.]*)(?=[\s/>]|$)", "tag", 1),
        _r(r"(?<=\s)([A-Za-z][\w-]*)(?==[\"{])", "attr", 1),
        (re.compile(rf"(?P<s>{_STR_DQ}|{_STR_SQ})|(?P<c>//.*$)"), {"s": "string", "c": "comment"}),
    ]
    ml = [_ML(r"/\*", r"\*/", "comment"), _ML(r"`", r"`", "string")]
    return Language(rules, ml, skip)


def _css():
    skip = rf"{_STR_DQ}|{_STR_SQ}"
    rules = [
        _r(r"[.][A-Za-z_-][\w-]*", "type"),
        _r(r"#[A-Za-z_-][\w-]*", "function"),
        _r(r"::?[A-Za-z-]+(?:\([^)]*\))?", "special"),
        _r(r"@[A-Za-z-]+", "keyword"),
        _r(r"(?<![\w-])(-{0,2}[A-Za-z][A-Za-z-]*)(?=\s*:[^{]*;|\s*:\s[^{,]*$)", "attr", 1),
        _r(r"[A-Za-z-]+(?=\()", "function"),
        _r(r"-?\b\d*\.?\d+(?:px|em|rem|%|vh|vw|vmin|vmax|s|ms|deg|fr|ch|pt)?", "number"),
        _r(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b(?=[\s;,)]|$)", "number"),
        _r(r"!important", "keyword"),
        (re.compile(rf"(?P<s>{_STR_DQ}|{_STR_SQ})"), {"s": "string"}),
    ]
    return Language(rules, [_ML(r"/\*", r"\*/", "comment")], skip)


def _html():
    js, css = _javascript(), _css()
    rules = [
        _r(r"<!(?i:doctype)[^>]*>", "special"),
        _r(r"</?([A-Za-z][\w:-]*)", "tag", 1),
        _r(r"</?(?=[A-Za-z!])|/?>", "punct"),
        _r(r"(?<=\s)([\w:@.\-]+)(?==)", "attr", 1),
        _r(r"=\s*(\"[^\"]*\"|'[^']*')", "string", 1),
        _r(r"&#?\w+;", "special"),
        _r(r"\{%.*?%\}", "keyword"),
        _r(r"\{\{.*?\}\}", "template"),
        _r(r"\{#.*?#\}", "comment"),
    ]
    ml = [
        _ML(r"<!--", r"-->", "comment"),
        _ML(r"<script\b[^>]*>", r"</script\s*>", inner=js),
        _ML(r"<style\b[^>]*>", r"</style\s*>", inner=css),
    ]
    return Language(rules, ml)


def _json():
    rules = [
        (re.compile(r'"(?:[^"\\\n]|\\.)*"?'), {0: "string"}),
        _r(r'"(?:[^"\\\n]|\\.)*"(?=\s*:)', "attr"),
        _r(r"-?\b\d+\.?\d*(?:[eE][+-]?\d+)?\b", "number"),
        _r(r"\b(?:true|false|null)\b", "special"),
    ]
    return Language(rules)


def _markdown():
    rules = [
        _r(r"^\s*(?:[-*+]|\d+\.)\s", "special"),
        _r(r"\*\*[^*]+\*\*|__[^_]+__", "type"),
        _r(r"`[^`]+`", "string"),
        _r(r"\[([^\]]+)\]", "attr", 1),
        _r(r"\]\(([^)]+)\)", "string", 1),
        _r(r"^>.*$", "comment", 0, re.M),
        _r(r"^\s{0,3}#{1,6}\s.*$", "keyword"),
    ]
    return Language(rules, [_ML(r"^\s*```", r"^\s*```", "string")])


_BUILDERS = {
    "python": _python, "javascript": _javascript, "html": _html, "css": _css,
    "json": _json, "markdown": _markdown, "text": lambda: Language([]),
}
_CACHE = {}


def get_language(name):
    if name not in _CACHE:
        _CACHE[name] = _BUILDERS.get(name, _BUILDERS["text"])()
    return _CACHE[name]


# --- highlighter ----------------------------------------------------------

class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, document, language="python", theme="dark"):
        super().__init__(document)
        self.plain = QTextCharFormat()
        self.lang = get_language(language)
        self._build_formats(theme)

    def _build_formats(self, theme):
        pal = PALETTES.get(theme, PALETTES["dark"])
        self.fmts = {k: _fmt(pal[k], italic=(k == "comment")) for k in TOKEN_KEYS}

    def set_language(self, name):
        self.lang = get_language(name)
        self.rehighlight()

    def set_theme(self, theme):
        self._build_formats(theme)
        self.rehighlight()

    def _paint(self, m, mapping):
        for group, key in mapping.items():
            start = m.start(group)
            if start >= 0:
                self.setFormat(start, m.end(group) - start, self.fmts[key])

    def _paint_region(self, text, ml, start, end):
        if end <= start:
            return
        if ml.inner is None:
            self.setFormat(start, end - start, self.fmts[ml.key])
            return
        self.setFormat(start, end - start, self.plain)
        for rx, mapping in ml.inner.rules:
            for m in rx.finditer(text, start, end):
                self._paint(m, mapping)

    def highlightBlock(self, text):
        lang = self.lang
        self.setCurrentBlockState(0)
        for rx, mapping in lang.rules:
            for m in rx.finditer(text):
                self._paint(m, mapping)
        if not lang.scan:
            return

        pos = 0
        state = self.previousBlockState()
        if state > 0:
            ml = lang.ml[state - 1]
            end = ml.end.search(text)
            if not end:
                self._paint_region(text, ml, 0, len(text))
                self.setCurrentBlockState(state)
                return
            self._paint_region(text, ml, 0, end.start() if ml.inner else end.end())
            pos = end.end()

        while pos <= len(text):
            m = lang.scan.search(text, pos)
            if not m:
                break
            if m.lastgroup == "skip":
                pos = m.end() if m.end() > m.start() else m.end() + 1
                continue
            idx = int(m.lastgroup[2:])
            ml = lang.ml[idx]
            end = ml.end.search(text, m.end())
            first = m.end() if ml.inner else m.start()
            if not end:
                self._paint_region(text, ml, first, len(text))
                self.setCurrentBlockState(idx + 1)
                break
            self._paint_region(text, ml, first, end.start() if ml.inner else end.end())
            pos = end.end()
