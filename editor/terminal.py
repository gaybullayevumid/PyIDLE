import codecs
import os
import re
import subprocess
import sys

from PyQt6.QtCore import QProcess, QProcessEnvironment, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07")
IS_WIN = sys.platform == "win32"


class HistoryLine(QLineEdit):
    submitted = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.history = []
        self.pos = 0
        self.returnPressed.connect(self._submit)

    def _submit(self):
        text = self.text()
        if text.strip() and (not self.history or self.history[-1] != text):
            self.history.append(text)
        self.pos = len(self.history)
        self.clear()
        self.submitted.emit(text)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up and self.history:
            self.pos = max(0, self.pos - 1)
            self.setText(self.history[self.pos])
        elif event.key() == Qt.Key.Key_Down and self.history:
            self.pos = min(len(self.history), self.pos + 1)
            self.setText(self.history[self.pos] if self.pos < len(self.history) else "")
        else:
            super().keyPressEvent(event)


class Terminal(QDockWidget):
    started = pyqtSignal()
    finished = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__("Terminal", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.cwd = os.path.expanduser("~")
        self.proc = None
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

        # sarlavha: nom + tugmalar
        bar = QWidget()
        bar.setObjectName("terminalBar")
        row = QHBoxLayout(bar)
        row.setContentsMargins(12, 4, 8, 4)
        title = QLabel("TERMINAL")
        title.setObjectName("explorerTitle")
        row.addWidget(title)
        row.addStretch()
        for text, slot in (("Stop", self.stop), ("Clear", self.clear)):
            btn = QToolButton()
            btn.setText(text)
            btn.setObjectName("terminalButton")
            btn.clicked.connect(slot)
            row.addWidget(btn)
        self.setTitleBarWidget(bar)

        self.output = QPlainTextEdit()
        self.output.setObjectName("terminalOutput")
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 10))
        self.output.setMaximumBlockCount(5000)

        self.prompt = QLabel()
        self.prompt.setObjectName("terminalPrompt")
        self.input = HistoryLine()
        self.input.setObjectName("terminalInput")
        self.input.setFont(QFont("Consolas", 10))
        self.input.submitted.connect(self._on_input)
        line = QHBoxLayout()
        line.setContentsMargins(8, 2, 8, 6)
        line.addWidget(self.prompt)
        line.addWidget(self.input, 1)

        body = QWidget()
        col = QVBoxLayout(body)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        col.addWidget(self.output, 1)
        col.addLayout(line)
        self.setWidget(body)
        self._update_prompt()

    # --- holat ---
    def set_cwd(self, folder):
        if folder and os.path.isdir(folder):
            self.cwd = folder
            self._update_prompt()

    def is_running(self):
        return self.proc is not None and self.proc.state() != QProcess.ProcessState.NotRunning

    def _update_prompt(self):
        self.prompt.setText(os.path.basename(self.cwd.rstrip("\\/")) or self.cwd)
        self.prompt.setToolTip(self.cwd)

    def focus_input(self):
        self.input.setFocus()

    # --- chiqish ---
    def write(self, text):
        text = ANSI.sub("", text).replace("\r\n", "\n").replace("\r", "\n")
        cur = self.output.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        cur.insertText(text)
        self.output.setTextCursor(cur)
        self.output.ensureCursorVisible()

    def clear(self):
        self.output.clear()

    # --- buyruqlar ---
    def _on_input(self, text):
        if self.is_running():
            self.write(text + "\n")
            self.proc.write((text + "\n").encode("utf-8"))
            return
        self.run(text)

    def run(self, cmdline, cwd=None):
        cmdline = cmdline.strip()
        if not cmdline:
            return False
        if self.is_running():
            self.write("[Avval joriy jarayonni to'xtating (Stop)]\n")
            return False
        if cwd:
            self.set_cwd(cwd)
        self.write(f"{self.prompt.text()}> {cmdline}\n")
        if self._builtin(cmdline):
            return True

        self.proc = QProcess(self)
        self.proc.setWorkingDirectory(self.cwd)
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        env.insert("PYTHONIOENCODING", "utf-8")
        env.insert("FORCE_COLOR", "0")
        self.proc.setProcessEnvironment(env)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._read)
        self.proc.errorOccurred.connect(self._error)
        self.proc.finished.connect(self._done)
        if IS_WIN:
            self.proc.setProgram("cmd.exe")
            self.proc.setArguments(["/d", "/s", "/c"])
            self.proc.setNativeArguments(f'"{cmdline}"')
        else:
            self.proc.setProgram("/bin/sh")
            self.proc.setArguments(["-c", cmdline])
        self._decoder.reset()
        self.proc.start()
        self.started.emit()
        return True

    def _builtin(self, cmdline):
        parts = cmdline.split(None, 1)
        if parts[0] == "cls" or parts[0] == "clear":
            self.clear()
            return True
        if parts[0] == "cd" and len(parts) == 2:
            target = os.path.expanduser(parts[1].strip().strip('"'))
            target = os.path.normpath(os.path.join(self.cwd, target))
            if os.path.isdir(target):
                self.set_cwd(target)
            else:
                self.write("Papka topilmadi.\n")
            return True
        return False

    def _read(self):
        data = bytes(self.proc.readAllStandardOutput())
        self.write(self._decoder.decode(data))

    def _error(self, err):
        if err == QProcess.ProcessError.FailedToStart:
            self.write("[Jarayonni ishga tushirib bo'lmadi]\n")

    def _done(self, code, _status):
        self.write(f"\n[Jarayon tugadi, kod: {code}]\n")
        self.finished.emit(code)

    def stop(self):
        if not self.is_running():
            return
        pid = self.proc.processId()
        if IS_WIN and pid:
            # runserver / npm kabi bola jarayonlar bilan birga o'chiriladi
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
        else:
            self.proc.kill()
        self.write("[To'xtatildi]\n")
