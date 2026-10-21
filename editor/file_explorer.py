from PyQt6.QtCore import QDir, Qt, pyqtSignal
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QDockWidget, QLabel, QTreeView


class FileExplorer(QDockWidget):
    file_opened = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("Explorer", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)

        title = QLabel("EXPLORER")
        title.setObjectName("explorerTitle")
        self.setTitleBarWidget(title)

        self.model = QFileSystemModel()
        self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        for col in (1, 2, 3):
            self.tree.hideColumn(col)
        self.tree.doubleClicked.connect(self._on_double_click)
        self.setWidget(self.tree)

    def set_root(self, folder):
        self.model.setRootPath(folder)
        self.tree.setRootIndex(self.model.index(folder))
        self.setWindowTitle(folder)

    def _on_double_click(self, index):
        if not self.model.isDir(index):
            self.file_opened.emit(self.model.filePath(index))
