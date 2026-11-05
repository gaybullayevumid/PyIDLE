from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFontComboBox,
    QFormLayout,
    QSpinBox,
)

DEFAULTS = {
    "theme": "dark",
    "font_family": "Consolas",
    "font_size": 11,
    "word_wrap": False,
    "last_folder": "",
}


class Settings:
    def __init__(self):
        self._s = QSettings("PyIDLE", "PyIDLE")

    def get(self, key):
        default = DEFAULTS[key]
        value = self._s.value(key, default)
        if isinstance(default, bool):
            return value in (True, "true", "True", 1, "1")
        if isinstance(default, int):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default
        return value

    def set(self, key, value):
        self._s.setValue(key, value)


settings = Settings()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        form = QFormLayout(self)

        self.theme = QComboBox()
        self.theme.addItems(["dark", "light"])
        self.theme.setCurrentText(settings.get("theme"))
        form.addRow("Theme", self.theme)

        self.font = QFontComboBox()
        self.font.setCurrentText(settings.get("font_family"))
        form.addRow("Font", self.font)

        self.size = QSpinBox()
        self.size.setRange(6, 40)
        self.size.setValue(settings.get("font_size"))
        form.addRow("Font size", self.size)

        self.wrap = QCheckBox("Uzun qatorlarni o'rash")
        self.wrap.setChecked(settings.get("word_wrap"))
        form.addRow("", self.wrap)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def save(self):
        settings.set("theme", self.theme.currentText())
        settings.set("font_family", self.font.currentFont().family())
        settings.set("font_size", self.size.value())
        settings.set("word_wrap", self.wrap.isChecked())
