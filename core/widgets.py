# holds costum ui widgets
# TODO: coverExists

from PySide6 import QtGui, QtCore, QtWidgets
from audiobook import Audiobook

class TreeWidget(QtWidgets.QTreeWidget, Audiobook):
    """Costum QTreeWidget"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setGeometry(*args["geometry"])
        self.setHeaderLabels(["Audiobook (0/0)", "Duration"])
        self.header().resizeSection(0, args["geometry"][2]-110)
        self.header().setStretchLastSection(True)        
        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
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
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            audiobook_data: dict = self.audiobook_default_data()
            for each_path in event.mimeData().urls():
                if QtCore.QFileInfo(each_path.path()).isDir():
                    pass
                else:
                    meta_data = self.get_meta_data(each_path.path())                    
                    if "name" in audiobook_data:
                        title = meta_data["title"]
                        audiobook_data[title] = audiobook_data.pop("name")
                        audiobook_data[title]["title"] = meta_data["title"]
                        audiobook_data[title]["author"] = meta_data["author"]
                    audiobook_data[title]["files"].append(dict(file=each_path.path(),
                                                               duration=meta_data["duration"]))
            for e in audiobook_data.keys():
                print(e)
                for i in audiobook_data[e].keys():
                    print(i, audiobook_data[e][i])
        else:
            super().dropEvent(event)

    def add_parent_item(self) -> QtWidgets.QTreeWidgetItem:
        parent_item = TreeWidgetItem()
        parent_item.add_user_inputs(parent=self)
        parent_item.setSizeHint(0, QtCore.QSize(100, 100))
        return parent_item
    
    def add_child_item(self, args: dict) -> None:
        child_item = TreeWidgetItem()
        args["parent"].addChild(child_item)
        child_item.set_text(args)
    
    def create_tree(self, audiobook_data: dict) -> None:
        for e_audiobook in audiobook_data.keys():
            # create parent item
            audiobook = self.add_parent_item()
            # edit user inputs with audiobook_data infos
            for input in audiobook.user_inputs.keys():
                if not input in audiobook_data[e_audiobook]:
                    continue
                input_widget = audiobook.user_inputs[input]
                if isinstance(input_widget, TextField):
                    input_widget.setText(audiobook_data[e_audiobook][input])
                elif isinstance(input_widget, BookCover):
                    input_widget.cover.load(audiobook_data[e_audiobook][input])
                    input_widget.setPixmap(input_widget.cover.scaledToHeight(70))
                elif isinstance(input_widget, Label):
                    input_widget.setText(audiobook_data[e_audiobook][input])
                elif isinstance(input_widget, ExportOptions):
                    input_widget.setCurrentIndex(audiobook_data[e_audiobook][input])
                elif isinstance(input_widget, ToggleButton):
                    input_widget.toggleColor("DarkGreen" if audiobook_data[e_audiobook][input] else "DarkRed")
            # add all files als children    
            for eFile in audiobook_data[e_audiobook]["files"]:
                self.add_child_item(dict(parent=audiobook,
                                         file=eFile["file"],
                                         duration=eFile["duration"]))
        # ??in extra function??
        if len(audiobook_data.keys()):
            self.help_text.hide()
            self.setHeaderLabels([f"Audiobook (0/{len(audiobook_data.keys())})", "Duration"])
        

class TreeWidgetItem(QtWidgets.QTreeWidgetItem):
    """Costum QTreeWidgetItem""" 
    def __init__(self) -> None:
        super().__init__()
        self.setFlags(QtCore.Qt.ItemIsEnabled |
                      QtCore.Qt.ItemIsSelectable |
                      QtCore.Qt.ItemIsDropEnabled)
        self.user_inputs = {}
    
    def set_text(self, args: dict) -> None:
        self.setText(0, args["file"])
        self.setText(1, args["duration"])

    def add_user_inputs(self, parent: QtWidgets.QTreeWidget) -> None:
        parent.addTopLevelItem(self)
        # qwidget sets scale and style for column 0 & 1
        column0_style = QtWidgets.QWidget()
        column0_style.setObjectName("c0")
        column0_style.setStyleSheet("QWidget#c0 {background-color: DarkGray;\
                                                 border-top-left-radius: 10px;\
                                                 border-bottom-left-radius: 10px;\
                                                 margin: 5px 0px 5px 0px;}")
        parent.setItemWidget(self, 0, column0_style)
        column1_style = QtWidgets.QWidget()
        column1_style.setObjectName("c1")
        column1_style.setStyleSheet("QWidget#c1 {background-color: DarkGray;\
                                                 border-top-right-radius: 10px;\
                                                 border-bottom-right-radius: 10px;\
                                                 margin: 5px 5px 5px 0px;}")
        parent.setItemWidget(self, 1, column1_style)
        # audiobook editing widgets
        activate_export = ToggleButton(dict(name="", 
                                          parent=column0_style,
                                          geometry=[0, 0, 20, 100],
                                          tip="",
                                          action=""))
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
        book_duration = Label(dict(text="Duration",
                                 parent=column1_style,
                                 position=[4, 40]))
        # add user input field for later edits
        self.user_inputs.update({"export": activate_export,
                                 "cover": book_cover,
                                 "title": book_title,
                                 "author": book_author,
                                 "quality": book_quality,
                                 "duration": book_duration,
                                 "destination": book_export})


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


class ToggleButton(QtWidgets.QPushButton):
    """Costum Toggle QPushButton"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setGeometry(*args["geometry"])
        self.setText(args["name"])
        self.setStyleSheet("QPushButton {background-color: transparent;\
                                         border-top-left-radius: 10px;\
                                         border-bottom-left-radius: 10px;\
                                         margin: 5px 5px 5px 0px;}")
        self.setToolTip(args["tip"])
        # Signals
        #self.clicked.connec(args["action"])

    def toggleColor(self, color: str):
        self.setStyleSheet(self.styleSheet().replace("transparent", color))


class Label(QtWidgets.QLabel):
    """Costum QLabel"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.move(*args["position"])
        self.setText(args["text"])


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
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                # ????everything will be converted to png and deleted
                self.cover.load(url.path())
                self.setPixmap(self.cover.scaledToHeight(70))
                event.acceptProposedAction()

        else:
            super().dropEvent(event)


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


        

        

    

