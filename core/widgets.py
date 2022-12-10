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
        self.header().resizeSection(0, args["geometry"][2]-100)
        self.header().setStretchLastSection(True)
        ###?????
        self.horizontalScrollBarPolicy(QtWidgets.QAbstractItemView.ScrollBarAlwaysOff)
        self.horizontalScrollBar().hide()
        self.horizontalScrollBar().resize(0, 0)
        
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
    
    def add_parent_item(self):
        TreeWidgetItem(dict(parent=self))


class TreeWidgetItem(QtWidgets.QTreeWidgetItem):
    """Costum QTreeWidgetItem""" 
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setText(0, "item_titel")
        self.setText(1, "item_length")
        args["parent"].addTopLevelItem(self)
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDropEnabled)
