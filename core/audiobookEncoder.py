__author__: str = "Dennis Oesterle"
__copyright__: str = "Copyright 2011-2022, Dennis Oesterle"
__license__: str = "CC BY-NC-SA - Attribution-NonCommercial-ShareAlike"
__appname__: str = "Audiobook Encoder"
__version__: str = "1.0"
__email__: str = "dennis.oesterle@icloud.com"

from PySide6.QtWidgets import QApplication, QMainWindow, QMenuBar
from PySide6.QtGui import QIcon
from PySide6.QtCore import QDir
from widgets import TreeWidget, PushButton
import sys


class AudiobookEncoderMainWindow(QMainWindow):
    """Create the main window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__appname__} - {__version__}")
        self.window_size: dict[str, int] = dict(x=1200, y=720)
        self.setFixedSize(self.window_size["x"], self.window_size["y"])
        #???self.setWindowIcon(QIcon(QDir.currentPath()+"/AudiobookEncoder/core/icons/icon32.png"))
        #menubar: QMenuBar = self.menuBar()
        #main_menu = menubar.addMenu("")
        #about_m = main_menu.addAction("About")

        self.audiobook_tree: TreeWidget = TreeWidget(dict(parent=self,
                                                          geometry=[10, 10, 
                                                          self.window_size["x"]-20,
                                                          self.window_size["y"]-50]))                
        
        PushButton(dict(name="Export", 
                        parent=self,
                        geometry=[10, 680, 160, 35],
                        tip="Batch export all audiobooks.",
                        action=""))


def main():
    app: QApplication = QApplication(sys.argv)
    #app.setWindowIcon(QIcon(QDir.currentPath()+"/AudiobookEncoder/core/icons/icon324.png"))
    mainwindow: QMainWindow = AudiobookEncoderMainWindow()
    mainwindow.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()