import ast
import json

PAIRS = {")": "(", "]": "[", "}": "{"}


def lint(lang, text):
    """Xatolar ro'yxati: [(qator (1 dan), ustun (0 dan), xabar)]."""
    if not text.strip():
        return []
    if lang == "python":
        return _python(text)
    if lang == "json":
        return _json(text)
    if lang in ("javascript", "css"):
        return _brackets(text, comments=("//", "/*", "*/") if lang == "javascript" else (None, "/*", "*/"))
    return []


def _python(text):
    try:
        ast.parse(text)
    except SyntaxError as e:
        return [(max(1, e.lineno or 1), max(0, (e.offset or 1) - 1), e.msg)]
    except ValueError as e:  # null bytes va h.k.
        return [(1, 0, str(e))]
    return []


def _json(text):
    try:
        json.loads(text)
    except json.JSONDecodeError as e:
        return [(e.lineno, max(0, e.colno - 1), e.msg)]
    return []


def _brackets(text, comments):
    """Qavslar balansi (qator/blok izohlari va qator ichidagi stringlar hisobga olinmaydi)."""
    line_c, block_open, block_close = comments
    stack = []
    line = 1
    col = 0
    i = 0
    n = len(text)
    quote = None
    in_block = False
    while i < n:
        ch = text[i]
        if ch == "\n":
            line += 1
            col = 0
            if quote in ('"', "'"):
                quote = None
            i += 1
            continue
        if in_block:
            if text.startswith(block_close, i):
                in_block = False
                i += len(block_close)
                col += len(block_close)
                continue
        elif quote:
            if ch == "\\":
                i += 2
                col += 2
                continue
            if ch == quote:
                quote = None
        elif line_c and text.startswith(line_c, i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        elif text.startswith(block_open, i):
            in_block = True
            i += len(block_open)
            col += len(block_open)
            continue
        elif ch in "\"'" or (ch == "`" and line_c):
            quote = ch
        elif ch in "([{":
            stack.append((ch, line, col))
        elif ch in PAIRS:
            if not stack or stack[-1][0] != PAIRS[ch]:
                return [(line, col, f"Kutilmagan '{ch}'")]
            stack.pop()
        i += 1
        col += 1
    if stack:
        ch, ln, cl = stack[-1]
        return [(ln, cl, f"'{ch}' yopilmagan")]
    return []
