import json
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

IS_WIN = sys.platform == "win32"


def python_exe(folder=None):
    """Loyiha venv'i bo'lsa shuni, aks holda tizim Python'ini qaytaradi."""
    if folder:
        for venv in (".venv", "venv", "env"):
            exe = os.path.join(folder, venv, "Scripts" if IS_WIN else "bin", "python.exe" if IS_WIN else "python")
            if os.path.isfile(exe):
                return exe
    found = shutil.which("python") or shutil.which("python3") or shutil.which("py")
    if found:
        return found
    return None if getattr(sys, "frozen", False) else sys.executable


def q(path):
    return f'"{path}"'


def django_dir(folder):
    """manage.py joylashgan papka (loyiha ildizi yoki bevosita ichki papka)."""
    if not folder or not os.path.isdir(folder):
        return None
    if os.path.isfile(os.path.join(folder, "manage.py")):
        return folder
    for name in sorted(os.listdir(folder)):
        sub = os.path.join(folder, name)
        if os.path.isfile(os.path.join(sub, "manage.py")):
            return sub
    return None


def npm_scripts(folder):
    """package.json dagi scripts: {nom: buyruq}."""
    if not folder:
        return {}
    try:
        with open(os.path.join(folder, "package.json"), encoding="utf-8") as f:
            return json.load(f).get("scripts", {}) or {}
    except (OSError, ValueError):
        return {}


def workdir(path, folder):
    if folder and os.path.commonpath([os.path.abspath(path), os.path.abspath(folder)]) == os.path.abspath(folder):
        return folder
    return os.path.dirname(os.path.abspath(path))


def command_for_file(path, folder):
    """Faylni ishga tushirish: ("shell", cmdline, cwd) | ("browser", path) | ("error", xabar)."""
    ext = os.path.splitext(path)[1].lower()
    name = os.path.basename(path).lower()
    cwd = workdir(path, folder)
    if ext in (".html", ".htm"):
        return ("browser", path)
    if ext in (".py", ".pyw"):
        py = python_exe(folder)
        if not py:
            return ("error", "Python topilmadi. Python'ni o'rnating yoki PATH ga qo'shing.")
        if name == "manage.py":
            return ("shell", f"{q(py)} -u {q(path)} runserver", os.path.dirname(path))
        return ("shell", f"{q(py)} -u {q(path)}", cwd)
    if ext in (".js", ".mjs", ".cjs"):
        if not shutil.which("node"):
            return ("error", "Node.js topilmadi. https://nodejs.org dan o'rnating.")
        return ("shell", f"node {q(path)}", cwd)
    if ext in (".jsx", ".tsx", ".ts", ".css"):
        scripts = npm_scripts(folder)
        for key in ("dev", "start"):
            if key in scripts:
                return ("shell", f"npm run {key}", folder)
        return ("error", "Bu fayl to'g'ridan-to'g'ri ishlamaydi. React loyihada Run > npm scripts dan foydalaning.")
    return ("error", f"'{ext or name}' fayllarini ishga tushirib bo'lmaydi.")


def open_in_browser(path):
    webbrowser.open(Path(os.path.abspath(path)).as_uri())


def launch_external(cmdline, cwd=None):
    """Interaktiv buyruq (masalan createsuperuser) uchun alohida konsol oynasi."""
    if IS_WIN:
        subprocess.Popen(["cmd.exe", "/k", cmdline], cwd=cwd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        return True
    for term in ("x-terminal-emulator", "gnome-terminal", "konsole", "xterm"):
        if shutil.which(term):
            subprocess.Popen([term, "-e", "sh", "-c", f"{cmdline}; exec $SHELL"], cwd=cwd)
            return True
    return False


# --- loyiha shablonlari -----------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <h1>{name}</h1>
  <button id="btn">Bosing</button>
  <p id="out"></p>
  <script src="script.js"></script>
</body>
</html>
"""

CSS_TEMPLATE = """* { box-sizing: border-box; }

body {
  font-family: system-ui, sans-serif;
  margin: 0;
  padding: 2rem;
  background: #f5f5f5;
  color: #222;
}

button {
  padding: 0.5rem 1rem;
  border: 0;
  border-radius: 6px;
  background: #0078d4;
  color: #fff;
  cursor: pointer;
}
"""

JS_TEMPLATE = """const btn = document.getElementById("btn");
const out = document.getElementById("out");
let count = 0;

btn.addEventListener("click", () => {
  count++;
  out.textContent = `Bosildi: ${count}`;
});
"""


def create_html_project(parent, name):
    """index.html + style.css + script.js. Yaratilgan papka yo'lini qaytaradi."""
    root = os.path.join(parent, name)
    os.makedirs(root, exist_ok=True)
    files = {"index.html": HTML_TEMPLATE.format(name=name), "style.css": CSS_TEMPLATE, "script.js": JS_TEMPLATE}
    for fname, content in files.items():
        path = os.path.join(root, fname)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
    return root


def django_new_project(folder, name):
    py = python_exe(folder)
    return f"{q(py)} -m django startproject {name}" if py else None


def react_new_project(name):
    return f"npm create vite@latest {name} -- --template react"
