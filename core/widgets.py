from PySide6.QtWidgets import (QWidget, QTreeWidget, QAbstractItemView, QTreeWidgetItem,
                               QLabel, QPushButton, QLineEdit, QComboBox, QFileDialog,
                               QMenu, QWidgetAction, QGridLayout)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QSize, QFileInfo, QStandardPaths
from datetime import timedelta
from audiobook import Audiobook, Preset, AudioPlayer


class TreeWidget(QTreeWidget):
    """Costum QTreeWidget"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setGeometry(*args["geometry"])
        self.setHeaderLabels(["Audiobook (0/0)", "Duration"])
        self.header().resizeSection(0, args["geometry"][2]-110)
        self.header().setStretchLastSection(True)
        self.setAnimated(True)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # help text
        self.help_text: QLabel = QLabel("Drag and Drop <br> Audiobooks", self)
        self.help_text.move(self.rect().center() - self.help_text.rect().center())
        self.help_text.setStyleSheet("QLabel {font-size: 25px;\
                                              font-weight: bold;\
                                              qproperty-alignment: AlignCenter;\
                                              color: grey;}")
        self.create_tree(Audiobook().read_data())
        self.setCurrentItem(self.topLevelItem(0))
        self.audio_player: AudioPlayer = AudioPlayer(self)
        self.last_played_item: TreeWidgetItem | bool = False

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        """Drag checks for external data or internal QTreewidgetItem movement"""
        if self.selectedItems():
            if isinstance(self.selectedItems()[0], TreeWidgetItem):
                root_item: QTreeWidgetItem = self.invisibleRootItem()
                # disable drop events for main treewidget
                root_item.setFlags(root_item.flags() & ~Qt.ItemIsDropEnabled)
                for parent_item_index in range(root_item.childCount()):
                    parent_item: TreeWidgetItem = self.topLevelItem(parent_item_index)
                    if parent_item == self.selectedItems()[0].parent():
                        continue
                    # disable drop events to avoid moving items between parent items
                    parent_item.setFlags(parent_item.flags() & ~Qt.ItemIsDropEnabled)
        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        """Drop QTreeItemWidgets, folders or files into widget"""
        if event.mimeData().hasUrls():
            data: dict = Audiobook().get_data(event.mimeData().urls())
            if not data:
                return
            self.create_tree(data)
        else:
            items: TreeWidgetItem = self.selectedItems()
            # get indices of selected QTreeWidgetItems before drop event
            indices: int = [self.indexFromItem(i).row() for i in items]
            super().dropEvent(event)
            json_data: dict = Audiobook().read_data()
            # get files from json by indices
            files: list[dict] = [json_data[items[0].args["audiobook_key"]]["files"][index] for index in indices]
            # delete files from json
            [json_data[items[0].args["audiobook_key"]]["files"].remove(f_dict) for f_dict in files]
            dropped_index: int = self.indexFromItem(items[0]).row()
            # insert files in json at new QTreeWidget index
            json_data[items[0].args["audiobook_key"]]["files"][dropped_index:dropped_index] = files
            Audiobook().save_data(json_data)

    def keyPressEvent(self, event) -> None:
        parent_item_count: int = self.invisibleRootItem().childCount()
        # delete audiobooks or files
        if (event.modifiers() == Qt.ControlModifier and
            event.key() == Qt.Key_Backspace):
                for each_item in self.selectedItems():
                    if not each_item.text(0):
                        # delete parent items
                        self.invisibleRootItem().removeChild(each_item)
                        Audiobook().delete_data(dict(audiobook_key=each_item.args["audiobook_key"]))
                        continue
                    # delete child items
                    each_item.parent().removeChild(each_item)
                    Audiobook().delete_data(dict(audiobook_key=each_item.args["audiobook_key"],
                                                 file=each_item.text(0)))
                self.parent_item_counter_update()
        # walk up the treewidget items
        if event.key() == Qt.Key_Up:
            if self.selectedItems():
                item_index: int = self.indexFromItem(self.selectedItems()[0]).row()
                if (not item_index and
                    self.selectedItems()[0].childCount()):
                        # select last item
                        self.setCurrentItem(self.topLevelItem(parent_item_count-1))
                        return
                item_up: TreeWidgetItem = self.itemAbove(self.selectedItems()[0])
                self.setCurrentItem(item_up)
        # walk down the treewidget items
        if event.key() == Qt.Key_Down:
            if self.selectedItems():
                item_index: int = self.indexFromItem(self.selectedItems()[0]).row()
                if (self.selectedItems()[0].childCount() and
                    not self.selectedItems()[0].isExpanded() and
                    item_index == parent_item_count-1):
                        # select first item
                        self.setCurrentItem(self.topLevelItem(0))
                        return
                if (not self.selectedItems()[0].childCount() and
                    item_index == self.selectedItems()[0].parent().childCount()-1):
                    item_down: TreeWidgetItem = self.itemBelow(self.selectedItems()[0])
                    if not item_down:
                        self.setCurrentItem(self.topLevelItem(0))
                        return
                item_down: TreeWidgetItem = self.itemBelow(self.selectedItems()[0])
                self.setCurrentItem(item_down)
        # expand parent items
        if event.key() == Qt.Key_Right:
            for each_item in self.selectedItems():
                each_item.setExpanded(True)
        # jump to root tree item and collapse items
        if event.key() == Qt.Key_Left:
            selected_items: list[TreeWidgetItem] = self.selectedItems()
            self.clearSelection()
            items_to_collapse: list = []
            for each_item in selected_items:
                if each_item.text(0):
                    # child item widgets
                    items_to_collapse.append(each_item.parent())
                else:
                    # parent item widgets
                    items_to_collapse.append(each_item)
                    each_item.setExpanded(False)
                # select parent item widgets
                for each_item_collapse in items_to_collapse:
                    each_item_collapse.setSelected(True)
        # select all parent items cmd+a
        if (event.modifiers() == Qt.ControlModifier and
            event.key() == Qt.Key_A):
                self.clearSelection()
                for each_parent_item in range(parent_item_count):
                    self.setCurrentItem(self.topLevelItem(each_parent_item))
        # play or stop file playback
        if event.key() == Qt.Key_Space:
            selected_items: list[TreeWidgetItem] = self.selectedItems()
            if not selected_items or not "file" in selected_items[0].args:
                return
            self.audio_player.play_audio(selected_items[0].args["file"])
            # clean play indicator ui styling
            if self.last_played_item:
                revert_text: str = self.last_played_item.text(0).replace("\N{Black Right-Pointing Triangle} ", "")
                self.last_played_item.setText(0, revert_text)
            # set play indicator ui styling
            if self.audio_player.playing_state:
                text = f"\N{Black Right-Pointing Triangle} {selected_items[0].text(0)}"
                selected_items[0].setText(0, text)
                self.last_played_item = selected_items[0]

    def add_parent_item(self, audiobook_key: str) -> QTreeWidgetItem:
        parent_item: TreeWidgetItem = TreeWidgetItem(dict(audiobook_key=audiobook_key,
                                                          parent=self))
        parent_item.setFlags(parent_item.flags() & ~Qt.ItemIsDragEnabled)
        parent_item.add_user_inputs()
        parent_item.setSizeHint(0, QSize(100, 100))
        return parent_item

    def add_child_item(self, args: dict) -> None:
        child_item: TreeWidgetItem = TreeWidgetItem(args)
        child_item.setFlags(child_item.flags() & ~Qt.ItemIsDropEnabled)
        args["parent"].addChild(child_item)
        child_item.set_text(args)

    def create_tree(self, audiobook_data: dict) -> None:
        for e_audiobook in audiobook_data:
            # create parent item
            audiobook: TreeWidgetItem = self.add_parent_item(e_audiobook)
            # edit user inputs with audiobook_data infos
            for input in audiobook.user_inputs:
                if not input in audiobook_data[e_audiobook]:
                    continue
                input_widget: (TextField | BookCover |
                               Label | ExportOptions | ToggleButton) = audiobook.user_inputs[input]
                if isinstance(input_widget, TextField):
                    input_widget.setText(audiobook_data[e_audiobook][input])
                elif isinstance(input_widget, BookCover):
                    if not audiobook_data[e_audiobook][input]:
                        continue
                    input_widget.cover.load(audiobook_data[e_audiobook][input])
                    input_widget.setPixmap(input_widget.cover.scaledToHeight(70))
                    input_widget.show_buttons(True)
                elif isinstance(input_widget, Label):
                    input_widget.setText(str(timedelta(seconds=audiobook_data[e_audiobook][input])))
                elif isinstance(input_widget, ExportOptions):
                    input_widget.setCurrentIndex(audiobook_data[e_audiobook][input])
                elif isinstance(input_widget, ToggleButton):
                    input_widget.toggle_color("DarkGreen" if audiobook_data[e_audiobook][input]
                                                          else "DarkRed")
                    input_widget.args["state"] = True if audiobook_data[e_audiobook][input] else False
                    input_widget.args["function"] = self.parent_item_counter_update
            # add all files as children
            for eFile in audiobook_data[e_audiobook]["files"]:
                self.add_child_item(dict(parent=audiobook,
                                         file=eFile["file"],
                                         duration=eFile["duration"],
                                         audiobook_key=e_audiobook))
        self.parent_item_counter_update()

    def parent_item_counter_update(self) -> None:
        root_item: QTreeWidgetItem = self.invisibleRootItem()
        parent_item_count: int = root_item.childCount()
        if not parent_item_count:
            self.help_text.show()
            self.setHeaderLabels(["Audiobook (0/0)", "Duration"])
        else:
            parent_item_active: int = len([root_item.child(i) for i in range(parent_item_count)
                                                              if root_item.child(i).user_inputs["export"].args["state"]])
            self.help_text.hide()
            self.setHeaderLabels([f"Audiobook ({parent_item_active}/{parent_item_count})", "Duration"])


class TreeWidgetItem(QTreeWidgetItem):
    """Costum QTreeWidgetItem"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setFlags(Qt.ItemIsEnabled |
                      Qt.ItemIsSelectable |
                      Qt.ItemIsDropEnabled |
                      Qt.ItemIsDragEnabled)
        self.user_inputs: dict = {}
        self.args: dict = args

    def set_text(self, args: dict) -> None:
        self.setText(0, QFileInfo(args["file"]).fileName())
        self.setText(1, str(timedelta(seconds=round(args["duration"]))))

    def add_user_inputs(self) -> None:
        self.args["parent"].addTopLevelItem(self)
        # qwidget sets scale and style for column 0 & 1
        column0_style: QWidget = QWidget()
        column0_style.setObjectName("c0")
        column0_style.setStyleSheet("QWidget#c0 {background-color: DarkGray;\
                                                 border-top-left-radius: 10px;\
                                                 border-bottom-left-radius: 10px;\
                                                 margin: 5px 0px 5px 0px;}")
        self.args["parent"].setItemWidget(self, 0, column0_style)
        column1_style: QWidget = QWidget()
        column1_style.setObjectName("c1")
        column1_style.setStyleSheet("QWidget#c1 {background-color: DarkGray;\
                                                 border-top-right-radius: 10px;\
                                                 border-bottom-right-radius: 10px;\
                                                 margin: 5px 5px 5px 0px;}")
        self.args["parent"].setItemWidget(self, 1, column1_style)
        # audiobook editing widgets
        activate_export: ToggleButton = ToggleButton(dict(name="",
                                                          parent=column0_style,
                                                          geometry=[0, 0, 20, 100],
                                                          tip="",
                                                          action="",
                                                          audiobook_key=self.args["audiobook_key"]))
        book_cover: BookCover = BookCover(dict(parent=column0_style,
                                               audiobook_key=self.args["audiobook_key"]))
        book_title: TextField = TextField(dict(name="Title",
                                               tip="Title",
                                               parent=column0_style,
                                               geometry=[110, 20, 270, 25],
                                               audiobook_key=self.args["audiobook_key"]))
        book_author: TextField = TextField(dict(name="Author",
                                                tip="Author",
                                                parent=column0_style,
                                                geometry=[390, 20, 270, 25],
                                                audiobook_key=self.args["audiobook_key"]))
        book_presets: PushButton = PushButton(dict(name="\N{BLACK STAR}",
                                                   parent=column0_style,
                                                   geometry=[665, 17, 25, 30],
                                                   tip="",
                                                   action="author_preset",
                                                   user_inputs=dict()))
        book_quality: ExportOptions = ExportOptions(dict(options=Audiobook().quality_presets,
                                                         parent=column0_style,
                                                         geometry=[110, 55, 270, 25],
                                                         audiobook_key=self.args["audiobook_key"]))
        book_export: TextField = TextField(dict(name="Destination",
                                                tip="Export Destination",
                                                parent=column0_style,
                                                geometry=[390, 55, 270, 25],
                                                audiobook_key=self.args["audiobook_key"]))
        file_browser: PushButton = PushButton(dict(name="\N{LOWER SEVEN EIGHTHS BLOCK}",
                                                   parent=column0_style,
                                                   geometry=[665, 53, 25, 30],
                                                   tip="",
                                                   action="file_dialog",
                                                   user_inputs=dict(destination=book_export)))
        book_duration: Label = Label(dict(text="Duration",
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
        book_presets.args.update({"user_inputs": self.user_inputs})


class PushButton(QPushButton):
    """Costum QPushButton"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setVisible(True)
        if "geometry" in args.keys():
            self.setGeometry(*args["geometry"])
        self.setText(args["name"] if len(args["name"]) <= 35 else f"{args['name'][:30]}…")
        self.setToolTip(args["tip"])
        self.args: dict = args
        self.popMenu: QMenu
        # Signals
        if isinstance(args["action"], str):
            if args["action"] == "file_dialog":
                args["action"] = self.file_dialog
            elif args["action"] == "author_preset":
                self.setStyleSheet("QPushButton::menu-indicator {width: 0px;}")
                args["action"] = self.empty
                self.author_menu: PresetMenu = PresetMenu(self.args)
                self.setMenu(self.author_menu)
            else:
                args["action"] = self.empty
        self.clicked.connect(args["action"])

    def empty(self):
        """empty signal function to avoid errors"""
        pass

    def file_dialog(self):
        main_window: QWidget = self.parent()
        if self.args["user_inputs"]["destination"].text():
            open_path: str = self.args["user_inputs"]["destination"].text()
        else:
            open_path: str = QStandardPaths.standardLocations(QStandardPaths.DesktopLocation)[0]
        export_path: str = QFileDialog.getExistingDirectory(main_window, "Export destination...", open_path)
        if not export_path:
            export_path = open_path
        self.args["user_inputs"]["destination"].setText(export_path)


class PresetMenu(QMenu):
    """Costum QMenu"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.args: dict = args
        self.aboutToShow.connect(self.create_author_preset_menu)

    def create_author_preset_menu(self) -> None:
        """Create preset item menu"""
        self.clear()
        self.addAction("Save", self.save_author_preset)
        self.addSeparator()
        for each_preset in sorted(Preset().read_data()):
            self.addAction(PresetWidgetAction(dict(parent=self,
                                                   name=each_preset,
                                                   user_inputs=self.args["user_inputs"])))

    def save_author_preset(self) -> None:
        """Save user infomation from input widgets into json"""
        Preset().get_data(dict(author=self.args["user_inputs"]["author"].text(),
                               destination=self.args["user_inputs"]["destination"].text(),
                               quality=self.args["user_inputs"]["quality"].currentIndex()))
        self.create_author_preset_menu()


class PresetWidgetAction(QWidgetAction):
    """Costum QWidgetAction"""
    def __init__(self, args: dict) -> None:
        super().__init__(args["parent"])
        self.container: QWidget = QWidget()
        self.preset_button: PushButton = PushButton(dict(name=args["name"],
                                                         parent=self.container,
                                                         tip="Apply preset",
                                                         action=self.apply_author_preset))
        self.delete_button: PushButton = PushButton(dict(name="\N{HEAVY MULTIPLICATION X}",
                                                         parent=self.container,
                                                         tip="Delete preset",
                                                         action=self.delete_author_preset))
        self.container.setStyleSheet("QPushButton {border: none;\
                                              text-align: left;}\
                                      QPushButton:hover {background-color: rgb(0, 122, 255);}")
        self.grid_layout: QGridLayout = QGridLayout()
        self.grid_layout.addWidget(self.preset_button, 0, 0)
        self.grid_layout.addWidget(self.delete_button, 0, 1)
        self.grid_layout.setContentsMargins(18, 3, 5, 3)
        self.grid_layout.setSpacing(3)
        self.grid_layout.setColumnMinimumWidth(0, 200)
        self.container.setLayout(self.grid_layout)
        self.setDefaultWidget(self.container)
        self.args = args

    def apply_author_preset(self):
        data: dict = Preset().read_data()
        self.args["user_inputs"]["author"].setText(self.args["name"])
        for key, value in data[self.args["name"]].items():
            widget: TextField | ExportOptions = self.args["user_inputs"][key]
            if isinstance(widget, TextField):
                widget.setText(value)
            elif isinstance(widget, ExportOptions):
                    widget.setCurrentIndex(value)

    def delete_author_preset(self):
        Preset().delete_data(self.args["name"])
        self.deleteLater()


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
        self.args: dict = args
        self.args.update({"state": True,
                          "function": None})
        # Signals
        self.clicked.connect(self.toggle)

    def toggle_color(self, color: str) -> None:
        replace_color: str = self.styleSheet().split("background-color: ")[1].split(";")[0]
        self.setStyleSheet(self.styleSheet().replace(replace_color, color))

    def toggle(self) -> None:
        data: dict = Audiobook().read_data()
        audiobook_index: str = self.args["audiobook_key"]
        toggle_state: bool = data[audiobook_index]["export"]
        data[audiobook_index].update({"export": False if toggle_state else True})
        self.toggle_color("DarkRed" if toggle_state else "DarkGreen")
        self.args["state"] = False if toggle_state else True
        self.args["function"]()
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
        self.cover_text: str = "Drop <br> Cover"
        self.setText(self.cover_text)
        self.setGeometry(20, 10, 80, 80)
        self.setStyleSheet("QLabel {border-radius: 10px;\
                                    border: 2px dashed grey;\
                                    font-size: 15px;\
                                    qproperty-alignment: AlignCenter;\
                                    color: grey;}\
                            PushButton {background-color: rgba(255, 255, 255, 0);\
                                        font-weight: bold;\
                                        border-radius: 10px;}")
        self.setAcceptDrops(True)
        self.cover: QPixmap = QPixmap()
        self.delete_button: PushButton = PushButton(dict(parent=self,
                                                         geometry=[60, 0, 20, 20],
                                                         name="\N{HEAVY MULTIPLICATION X}",
                                                         tip="Delete cover",
                                                         action=self.delete_cover))
        self.delete_button.setVisible(False)
        self.resize_button: PushButton = PushButton(dict(parent=self,
                                                         geometry=[60, 60, 20, 20],
                                                         name="\N{WARNING SIGN}",
                                                         tip="Resize cover 1:1",
                                                         action=self.resize_cover))
        self.resize_button.setVisible(False)
        self.args: dict = args

    def show_buttons(self, state: bool) -> None:
        self.delete_button.setVisible(state)
        if self.cover.width() % self.cover.height():
            self.resize_button.setVisible(state)

    def delete_cover(self):
        Audiobook().delete_data(dict(cover="Delete",
                                     audiobook_key=self.args["audiobook_key"]))
        self.show_buttons(False)
        self.setText(self.cover_text)

    def resize_cover(self):
        path: str = Audiobook().resize_cover(self.args["audiobook_key"])
        self.cover.load(path)
        self.setPixmap(self.cover.scaledToHeight(70))
        self.show_buttons(True)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                self.cover.load(url.path())
                self.setPixmap(self.cover.scaledToHeight(70))
                event.acceptProposedAction()
                audiobook_index: str = self.args["audiobook_key"]
                data: dict = Audiobook().read_data()
                data[audiobook_index].update({"cover": url.path()})
                self.show_buttons(True)
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
        self.setToolTip(args["tip"])
        self.setStyleSheet("border-radius: 5px;\
                            border: 2px solid grey;\
                            background-color: DarkGray;")
        self.args: dict = args
        # Signals
        self.textChanged.connect(self.text_edited)

    def text_edited(self) -> None:
        data: dict = Audiobook().read_data()
        audiobook_index: str = self.args["audiobook_key"]
        audiobook_input: str = self.args["name"].lower()
        data[audiobook_index].update({audiobook_input: self.text()})
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
        self.args: dict = args
        # Signals
        self.currentIndexChanged.connect(self.index_changed)

    def index_changed(self) -> None:
        audiobook_index: str = self.args["audiobook_key"]
        data: dict = Audiobook().read_data()
        data[audiobook_index].update({"quality": self.currentIndex()})
        Audiobook().save_data(data)