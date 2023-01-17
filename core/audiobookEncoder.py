__author__: str = "Dennis Oesterle"
__copyright__: str = "Copyright 2011-2022, Dennis Oesterle"
__license__: str = "CC BY-NC-SA - Attribution-NonCommercial-ShareAlike"
__appname__: str = "Audiobook Encoder"
__version__: str = "1.0"
__email__: str = "dennis.oesterle@icloud.com"

from PySide6.QtWidgets import QApplication, QMainWindow, QMenuBar, QWidget
from PySide6.QtGui import QIcon, QAction, QPainter, QColor
from PySide6.QtCore import Qt, QDir
from widgets import TreeWidget, PushButton, GridLayout
import sys


class AudiobookEncoderMainWindow(QMainWindow):
    """Create the main window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__appname__} - {__version__}")
        self.window_size: dict[str, int] = dict(x=1200, y=720)
        self.resize(self.window_size["x"], self.window_size["y"])
        self.setMinimumWidth(self.window_size["x"])
        self.setMaximumWidth(self.window_size["x"])
        #???self.setWindowIcon(QIcon(QDir.currentPath()+"/AudiobookEncoder/core/icons/icon32.png"))
        menubar: QMenuBar = self.menuBar()
        main_menu = menubar.addMenu("")
        about_m = main_menu.addAction("About")
        about_m.setMenuRole(QAction.ApplicationSpecificRole)
        cental_widget: QWidget = QWidget(self)
        self.setCentralWidget(cental_widget)
        tree_widget: TreeWidget = TreeWidget(dict(geometry=[10, 10,
                                                            self.window_size["x"]-20,
                                                            self.window_size["y"]-50]))
        export_button: PushButton = PushButton(dict(name="Export",
                                                    parent=self,
                                                    fixed_height=33,
                                                    tip="Batch export all audiobooks.",
                                                    action="export"))
        grid_layout = GridLayout(dict(parent=cental_widget,
                                      margins=[10, 10, 10, 15],
                                      spacing=10))
        grid_layout.addWidget(tree_widget, 0, 0)
        grid_layout.addWidget(export_button, 1, 0)



def main() -> None:
    app: QApplication = QApplication(sys.argv)
    #app.setWindowIcon(QIcon(QDir.currentPath()+"/AudiobookEncoder/core/icons/icon324.png"))
    mainwindow: QMainWindow = AudiobookEncoderMainWindow()
    mainwindow.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()