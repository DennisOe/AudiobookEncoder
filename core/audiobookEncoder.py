from PySide6.QtWidgets import QApplication, QMainWindow, QMenuBar, QWidget
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QDir, QDateTime
from widgets import TreeWidget, PushButton, GridLayout, Dialog
import sys


__author__: str = "Dennis Oesterle"
__copyright__: str = f"Copyright 2011-{QDateTime().currentDateTime().date().year()}"
__license__: str = "CC BY-NC-SA - Attribution-NonCommercial-ShareAlike"
__appname__: str = "Audiobook Encoder"
__version__: str = "1.0"
__email__: str = "dennis.oesterle@icloud.com"


class AudiobookEncoderMainWindow(QMainWindow):
    """Create the main window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__appname__} - {__version__}")
        self.window_size: dict[str, int] = dict(x=1200, y=720)
        self.resize(self.window_size["x"], self.window_size["y"])
        self.setMinimumSize(960, 280)
        menubar: QMenuBar = self.menuBar()
        main_menu = menubar.addMenu("")
        about_m = main_menu.addAction("About",
                                      lambda: Dialog(self).about_ui(dict(version=__version__,
                                                                         copyright=__copyright__,
                                                                         license=__license__.split(" - "),
                                                                         email=__email__,
                                                                         author=__author__)))
        about_m.setMenuRole(QAction.ApplicationSpecificRole)
        cental_widget: QWidget = QWidget(self)
        self.setCentralWidget(cental_widget)
        self.tree_widget: TreeWidget = TreeWidget(dict(geometry=[10, 10,
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
        grid_layout.addWidget(self.tree_widget, 0, 0)
        grid_layout.addWidget(export_button, 1, 0)

    def resizeEvent(self, event) -> None:
        self.tree_widget.header().resizeSection(0, event.size().width()-130)


def main() -> None:
    app: QApplication = QApplication(sys.argv)
    app.setWindowIcon(QIcon(QDir.currentPath()+"/AudiobookEncoder/icons/app_icon.png"))
    mainwindow: QMainWindow = AudiobookEncoderMainWindow()
    mainwindow.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()