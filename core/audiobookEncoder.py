# main file for ui
# TODO: coverExists
# TODO: main ui
# TODO: 
# TODO: 
__author__ = "Dennis Oesterle"
__copyright__ = "Copyright 2011-2022, Dennis Oesterle"
__license__ = "CC BY-NC-SA - Attribution-NonCommercial-ShareAlike"
__appname__ = "Audiobook Encoder"
__version__ = "1.0"
__email__ = "dennis.oesterle@icloud.com"

from PySide6 import QtGui, QtCore, QtWidgets
import sys
from widgets import TreeWidget, PushButton


class AudiobookEncoderMainWindow(QtWidgets.QMainWindow):
    """Create the main window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__appname__} - {__version__}")
        self.window_size: dict[str, int] = dict(x=1200, y=720)
        self.setFixedSize(self.window_size["x"], self.window_size["y"])
        #???self.setWindowIcon(QtGui.QIcon(QtCore.QDir.currentPath()+"/AudiobookEncoder/core/icons/icon32.png"))
        #menubar: QtWidgets.QMenuBar = self.menuBar()
        #main_menu = menubar.addMenu("")
        #about_m = main_menu.addAction("About")

        
        self.audiobook_tree = TreeWidget(dict(parent=self,
                                              geometry=[10, 10, 
                                              self.window_size["x"]-20,
                                              self.window_size["y"]-50]))
        data = {"1 - Der super Papagai":
                    {"title": "1 - Der super Papagai",
                     "author": "Die drei Fragezeichen",
                     "genre": "Audiobook",
                     "cover": "/Users/dennisoesterle/Desktop/cover.jpg",
                     "length": "2:00",
                     "destination": "/Desktop/",
                     "quality": 1,
                     "files": [{"file": "/audiofile1.mp3", "length": "1:20"}, {"file": "/audiofile2.mp3", "length": "1:20"}, {"file": "/audiofile3.mp3", "length": "1:20"}, {"file": "/audiofile4.mp3", "length": "1:20"}], 
                     "export": True,
                    },
                }
        self.audiobook_tree.create_tree(data)
                
        
        PushButton(dict(name="Export", 
                        parent=self,
                        geometry=[10, 680, 160, 35],
                        tip="Batch export all audiobooks.",
                        action=""))


def main():
    app = QtWidgets.QApplication(sys.argv)
    #app.setWindowIcon(QtGui.QIcon(QtCore.QDir.currentPath()+"/AudiobookEncoder/core/icons/icon324.png"))
    mainwindow = AudiobookEncoderMainWindow()
    mainwindow.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()