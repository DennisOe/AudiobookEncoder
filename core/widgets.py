# holds costum ui widgets

from PySide6.QtWidgets import (QWidget, QTreeWidget, QAbstractItemView, QTreeWidgetItem, 
                               QLabel, QPushButton, QLineEdit, QComboBox)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QSize, QFileInfo
from datetime import timedelta
from audiobook import Audiobook


class TreeWidget(QTreeWidget):
    """Costum QTreeWidget"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setGeometry(*args["geometry"])
        self.setHeaderLabels(["Audiobook (0/0)", "Duration"])
        self.header().resizeSection(0, args["geometry"][2]-110)
        self.header().setStretchLastSection(True)        
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # help text
        self.help_text = QLabel("Drag and Drop <br> Audiobooks", self)
        self.help_text.move(self.rect().center() - self.help_text.rect().center())
        self.help_text.setStyleSheet("QLabel {font-size: 25px;\
                                              font-weight: bold;\
                                              qproperty-alignment: AlignCenter;\
                                              color: grey;}")
        self.create_tree(Audiobook().read_data())
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
            data: dict = Audiobook().get_data(event.mimeData().urls())
            self.create_tree(data)
        else:
            super().dropEvent(event)

    def keyPressEvent(self, event):
        if (event.modifiers() == Qt.ControlModifier and
            event.key() == Qt.Key_Backspace):
            # delete audiobooks or files
            root_item = self.invisibleRootItem()
            for each_item in self.selectedItems():
                if not each_item.text(0):
                    # delete parent items
                    root_item.removeChild(each_item)
                    Audiobook().delete_data(dict(audiobook_key=each_item.audiobook_key,
                                                 file=""))
                    continue
                # delete child items
                each_item.parent().removeChild(each_item)
                Audiobook().delete_data(dict(audiobook_key=each_item.audiobook_key,
                                             file=each_item.text(0)))

    def add_parent_item(self, audiobook_key: str) -> QTreeWidgetItem:
        parent_item = TreeWidgetItem(audiobook_key)
        parent_item.add_user_inputs(parent=self)
        parent_item.setSizeHint(0, QSize(100, 100))
        return parent_item
    
    def add_child_item(self, args: dict) -> None:
        child_item = TreeWidgetItem(args["audiobook_key"])
        args["parent"].addChild(child_item)
        child_item.set_text(args)
    
    def create_tree(self, audiobook_data: dict) -> None:
        for e_audiobook in audiobook_data.keys():
            # create parent item
            audiobook = self.add_parent_item(e_audiobook)
            # edit user inputs with audiobook_data infos
            for input in audiobook.user_inputs.keys():
                if not input in audiobook_data[e_audiobook]:
                    continue
                input_widget = audiobook.user_inputs[input]
                if isinstance(input_widget, TextField):
                    input_widget.setText(audiobook_data[e_audiobook][input])
                elif isinstance(input_widget, BookCover):
                    if not audiobook_data[e_audiobook][input]:
                        continue
                    input_widget.cover.load(audiobook_data[e_audiobook][input])
                    input_widget.setPixmap(input_widget.cover.scaledToHeight(70))
                elif isinstance(input_widget, Label):
                    input_widget.setText(str(timedelta(seconds=audiobook_data[e_audiobook][input])))
                elif isinstance(input_widget, ExportOptions):
                    input_widget.setCurrentIndex(audiobook_data[e_audiobook][input])
                elif isinstance(input_widget, ToggleButton):
                    input_widget.toggle_color("DarkGreen" if audiobook_data[e_audiobook][input]
                                                         else "DarkRed")
            # add all files als children    
            for eFile in audiobook_data[e_audiobook]["files"]:
                self.add_child_item(dict(parent=audiobook,
                                         file=QFileInfo(eFile["file"]).fileName(),
                                         duration=eFile["duration"],
                                         audiobook_key=e_audiobook))
        # ??in extra function??
        if len(audiobook_data.keys()):
            self.help_text.hide()
            self.setHeaderLabels([f"Audiobook (0/{len(audiobook_data.keys())})", "Duration"])
        

class TreeWidgetItem(QTreeWidgetItem):
    """Costum QTreeWidgetItem""" 
    def __init__(self, audiobook_key: str) -> None:
        super().__init__()
        self.setFlags(Qt.ItemIsEnabled |
                      Qt.ItemIsSelectable |
                      Qt.ItemIsDropEnabled)
        self.user_inputs: dict = {}
        self.audiobook_key = audiobook_key
    
    def set_text(self, args: dict) -> None:
        self.setText(0, args["file"])
        self.setText(1, str(timedelta(seconds=round(args["duration"]))))

    def add_user_inputs(self, parent: QTreeWidget) -> None:
        parent.addTopLevelItem(self)
        # qwidget sets scale and style for column 0 & 1
        column0_style = QWidget()
        column0_style.setObjectName("c0")
        column0_style.setStyleSheet("QWidget#c0 {background-color: DarkGray;\
                                                 border-top-left-radius: 10px;\
                                                 border-bottom-left-radius: 10px;\
                                                 margin: 5px 0px 5px 0px;}")
        parent.setItemWidget(self, 0, column0_style)
        column1_style = QWidget()
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
                                            action="",
                                            audiobook_key=self.audiobook_key))
        book_cover = BookCover(dict(parent=column0_style,
                                    audiobook_key=self.audiobook_key))
        book_title = TextField(dict(name="Title",
                                    parent=column0_style,
                                    geometry=[110, 20, 270, 25],
                                    audiobook_key=self.audiobook_key))
        book_author = TextField(dict(name="Author",
                                     parent=column0_style,
                                     geometry=[390, 20, 270, 25],
                                     audiobook_key=self.audiobook_key))
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
                                          geometry=[110, 55, 270, 25],
                                          audiobook_key=self.audiobook_key))
        book_export = TextField(dict(name="Destination",
                                     parent=column0_style,
                                     geometry=[390, 55, 270, 25],
                                     audiobook_key=self.audiobook_key))
        file_browser = PushButton(dict(name="F", 
                                       parent=column0_style,
                                       geometry=[630, 53, 25, 30],
                                       tip="",
                                       action=""))
        book_duration = Label(dict(text="Duration",
                                   parent=column1_style,
                                   geometry=[4, 40, 100, 20]))
        # add user input field for later edits
        self.user_inputs.update({"export": activate_export,
                                 "cover": book_cover,
                                 "title": book_title,
                                 "author": book_author,
                                 "quality": book_quality,
                                 "duration": book_duration,
                                 "destination": book_export})        


class PushButton(QPushButton):
    """Costum QPushButton"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setVisible(True)
        self.setGeometry(*args["geometry"])
        self.setText(args["name"])
        self.setToolTip(args["tip"])
        # Signals
        #self.clicked.connec(args["action"])


class ToggleButton(QPushButton):
    """Costum Toggle QPushButton"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setVisible(True)
        self.setGeometry(*args["geometry"])
        self.setText(args["name"])
        self.setStyleSheet("QPushButton {background-color: DarkGreen;\
                                         border-top-left-radius: 10px;\
                                         border-bottom-left-radius: 10px;\
                                         margin: 5px 5px 5px 0px;}")
        self.setToolTip(args["tip"])
        self.args = args
        # Signals
        self.clicked.connect(self.toggle)

    def toggle_color(self, color: str):
        replace_color: str = self.styleSheet().split("background-color: ")[1].split(";")[0]
        self.setStyleSheet(self.styleSheet().replace(replace_color, color))
    
    def toggle(self):
        data: dict = Audiobook().read_data()
        audiobook_index = self.args["audiobook_key"]
        toggle_state = data[audiobook_index]["export"]
        data[audiobook_index]["export"] = False if toggle_state else True
        self.toggle_color("DarkRed" if toggle_state else "DarkGreen")
        Audiobook().save_data(data)


class Label(QLabel):
    """Costum QLabel"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setVisible(True)
        self.setGeometry(*args["geometry"])
        self.setText(args["text"])


class BookCover(QLabel):
    """Costum QLabel to display artwork"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setVisible(True)
        self.setText("Drop <br> Cover")
        self.setToolTip("Double click to delete cover artwork.")
        self.setGeometry(20, 10, 80, 80)
        self.setStyleSheet("QLabel {border-radius: 10px;\
                                    border: 2px dashed grey;\
                                    font-size: 15px;\
                                    qproperty-alignment: AlignCenter;\
                                    color: grey;}")
        self.setAcceptDrops(True)
        self.cover = QPixmap()
        self.args = args
        # Signal
    
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
                audiobook_index = self.args["audiobook_key"]
                data = Audiobook().read_data()
                data[audiobook_index]["cover"] = url.path()
                Audiobook().save_data(data)
        else:
            super().dropEvent(event)


class TextField(QLineEdit):
    """Costum QLineEdit"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setVisible(True)
        self.setGeometry(*args["geometry"])
        self.setPlaceholderText(args["name"])
        self.setStyleSheet("border-radius: 5px;\
                            border: 2px solid grey;\
                            background-color: DarkGray;")
        self.args = args
        # Signals
        self.textEdited.connect(self.text_edited)
    
    def text_edited(self):
        data: dict = Audiobook().read_data()
        audiobook_index = self.args["audiobook_key"]
        audiobook_input = self.args["name"].lower()
        data[audiobook_index][audiobook_input] = self.text()
        Audiobook().save_data(data)


class ExportOptions(QComboBox):
    def __init__(self, args: dict) -> None: 
        super().__init__()
        self.setParent(args["parent"])
        self.setVisible(True)
        self.setGeometry(*args["geometry"])
        self.addItems(args["options"])
        self.setToolTip("Change quality of an audiobook.")
        self.setStyleSheet("border-radius: 5px;\
                            border: 2px solid grey;\
                            background-color: DarkGray;")
        self.args = args
        # Signals
        self.currentIndexChanged.connect(self.index_changed)

    def index_changed(self):
        audiobook_index = self.args["audiobook_key"]
        data = Audiobook().read_data()
        data[audiobook_index]["quality"] = self.currentIndex()
        Audiobook().save_data(data) 