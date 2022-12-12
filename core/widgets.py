# holds costum ui widgets
# TODO: coverExists

from PySide6 import QtGui, QtCore, QtWidgets


class PushButton(QtWidgets.QPushButton):
    """Costum QPushButton"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setGeometry(*args["geometry"])
        self.setText(args["name"])
        self.setToolTip(args["tip"])
        # Signals
        #self.clicked.connec(args["action"])


class TreeWidget(QtWidgets.QTreeWidget):
    """Costum QTreeWidget"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setGeometry(*args["geometry"])
        self.setHeaderLabels(["Audiobook (0/0)", "Duration"])
        self.header().resizeSection(0, args["geometry"][2]-110)
        self.header().setStretchLastSection(True)        
        self.setAcceptDrops(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        # help text
        self.help_text = QtWidgets.QLabel("Drag and Drop <br> Audiobooks", self)
        self.help_text.move(self.rect().center() - self.help_text.rect().center())
        self.help_text.setStyleSheet("QLabel {font-size: 25px;\
                                              font-weight: bold;\
                                              qproperty-alignment: AlignCenter;\
                                              color: grey;}")
        # Signals
        #self.itemSelectionChanged.connect(self.changeWidgets)
        #self.itemDoubleClicked.connect(self.openFolder)
    
    def add_parent_item(self, total_length: str) -> None:
        parent_item = TreeWidgetItem(dict(parent=self))
        parent_item.set_setup_menu()
        parent_item.setSizeHint(0, QtCore.QSize(100, 100))
    
    def add_child_item(self, text: list[str]) -> None: # anderen parent
        child_item = TreeWidgetItem(dict(parent=self))
        child_item.set_text(text)

class TreeWidgetItem(QtWidgets.QTreeWidgetItem):
    """Costum QTreeWidgetItem""" 
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.args = args
        self.args["parent"].addTopLevelItem(self)
        self.setFlags(QtCore.Qt.ItemIsEnabled |
                      QtCore.Qt.ItemIsSelectable |
                      QtCore.Qt.ItemIsDropEnabled)
    
    def set_text(self, text: list[str]) -> None:
        self.setText(0, text[0])
        self.setText(1, text[1])
    
    def set_setup_menu(self) -> None:
        # qwidget sets scale and style for column 0 & 1
        column0_style = QtWidgets.QWidget()
        column0_style.setObjectName("c0")
        column0_style.setStyleSheet("QWidget#c0 {background-color: DarkGray;\
                                                 border-top-left-radius: 10px;\
                                                 border-bottom-left-radius: 10px;\
                                                 margin: 5px 0px 5px 0px;}")
        self.args["parent"].setItemWidget(self, 0, column0_style)
        column1_style = QtWidgets.QWidget()
        column1_style.setObjectName("c1")
        column1_style.setStyleSheet("QWidget#c1 {background-color: DarkGray;\
                                                 border-top-right-radius: 10px;\
                                                 border-bottom-right-radius: 10px;\
                                                 margin: 5px 5px 5px 0px;}")
        self.args["parent"].setItemWidget(self, 1, column1_style)
        # audiobook editing widgets
        activate_export = PushButton(dict(name="", 
                                          parent=column0_style,
                                          geometry=[0, 0, 20, 100],
                                          tip="",
                                          action=""))
        activate_export.setStyleSheet("QPushButton {background-color: lightGreen;\
                                                    border-top-left-radius: 10px;\
                                                    border-bottom-left-radius: 10px;\
                                                    margin: 5px 5px 5px 0px;}")
        book_cover = BookCover(column0_style)
        book_title = TextField(dict(name="Title",
                                    parent=column0_style,
                                    geometry=[110, 20, 270, 25]))
        book_author = TextField(dict(name="Author",
                                     parent=column0_style,
                                     geometry=[390, 20, 270, 25]))
        book_presets = PushButton(dict(name="P", 
                                     parent=column0_style,
                                     geometry=[630, 17, 25, 30],
                                     tip="",
                                     action=""))
        book_quality = ExportOptions(dict(options=["96 Kbps, Stereo, 48 kHz",
                                                   "128 Kbps, Stereo, 48 kHz", 
                                                   "256 Kbps, Stereo, 48 kHz", 
                                                   "320 Kbps, Stereo, 48 kHz"],
                                          parent=column0_style,
                                          geometry=[110, 55, 270, 25]))
        book_export = TextField(dict(name="Export Destination",
                                     parent=column0_style,
                                     geometry=[390, 55, 270, 25]))
        file_browser = PushButton(dict(name="F", 
                                       parent=column0_style,
                                       geometry=[630, 53, 25, 30],
                                       tip="",
                                       action=""))



        book_length = QtWidgets.QLabel("Length", column1_style)
        book_length.move(4, 40)
    
class BookCover(QtWidgets.QLabel):
    """Costum QLabel to display artwork"""
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__()
        self.setParent(parent)
        self.setText("Drop <br> Cover")
        self.setToolTip("Double click to delete cover artwork.")
        self.setGeometry(20, 10, 80, 80)
        self.setStyleSheet("QLabel {border-radius: 10px;\
                                    border: 2px dashed grey;\
                                    font-size: 15px;\
                                    qproperty-alignment: AlignCenter;\
                                    color: grey;}")
        self.setAcceptDrops(True)
        self.cover = QtGui.QPixmap()

class TextField(QtWidgets.QLineEdit):
    """Costum QLineEdit"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setGeometry(*args["geometry"])
        self.setPlaceholderText(args["name"])
        self.setStyleSheet("border-radius: 5px;\
                            border: 2px solid grey;\
                            background-color: DarkGray;")
        # Signals

class ExportOptions(QtWidgets.QComboBox):
    def __init__(self, args: dict) -> None: 
        super().__init__()
        self.setParent(args["parent"])
        self.setGeometry(*args["geometry"])
        self.addItems(args["options"])
        self.setToolTip("Change quality of an audiobook.")
        self.setStyleSheet("border-radius: 5px;\
                            border: 2px solid grey;\
                            background-color: DarkGray;")
        # Signals


        

        

    

