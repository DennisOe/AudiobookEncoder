from PySide6.QtWidgets import (QWidget, QTreeWidget, QAbstractItemView, QTreeWidgetItem,
                               QLabel, QPushButton, QLineEdit, QComboBox, QFileDialog,
                               QMenu, QWidgetAction, QGridLayout, QDialog, QDialogButtonBox,
                               QPlainTextEdit, QProgressBar)
from PySide6.QtGui import QPixmap, QImageWriter, QDesktopServices
from PySide6.QtCore import Qt, QSize, QFileInfo, QStandardPaths, QUrl, QDir
from datetime import timedelta
from audiobook import Audiobook, Preset, AudioPlayer
from typing import Self



class TreeWidget(QTreeWidget):
    """Costum QTreeWidget"""
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setGeometry(*args["geometry"])
        self.setHeaderLabels(["Audiobook (0/0)", "Duration"])
        #self.header().resizeSection(0, args["geometry"][2]-110)
        self.header().setStretchLastSection(True)
        self.setAnimated(True)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # help text
        self.help_text: QLabel = QLabel("Drag and Drop <br> Audiobooks", self)
        self.help_text.setStyleSheet("QLabel {font-size: 25px;\
                                              font-weight: bold;\
                                              qproperty-alignment: AlignCenter;\
                                              color: grey;}")
        self.create_tree(Audiobook().read_data())
        self.setCurrentItem(self.topLevelItem(0))
        self.help_text.move(self.rect().center() - self.help_text.rect().center())
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
                        parent_item.setFlags(parent_item.flags() | Qt.ItemIsDropEnabled)
                        continue
                    # disable drop events to avoid moving items between parent items
                    parent_item.setFlags(parent_item.flags() & ~Qt.ItemIsDropEnabled)
        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        """Drop QTreeItemWidgets, folders or files into widget"""
        if event.mimeData().hasUrls():
            data: dict = Audiobook().get_data(event.mimeData().urls())
            if not data:
                Dialog(self).log_ui("Only MP3s are allowed. No files have been added.")
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
                parent_items: list[str] = []
                child_items: list[dict] = []
                for each_item in self.selectedItems():
                    if not each_item.text(0):
                        # delete parent items
                        self.invisibleRootItem().removeChild(each_item)
                        parent_items.append(each_item.args["audiobook_key"])
                        continue
                    # delete child items
                    each_item.parent().removeChild(each_item)
                    child_items.append(dict(audiobook_key=each_item.args["audiobook_key"],
                                            file=each_item.text(0)))
                if parent_items:
                    Audiobook().delete_data(dict(audiobook_keys=parent_items))
                if child_items:
                    json_data: dict = Audiobook().delete_data(dict(files=child_items))
                    self.parent_item_duration_update(json_data)
                self.parent_item_counter_update()
        # walk up the treewidget items
        if event.key() == Qt.Key_Up:
            if self.selectedItems():
                item_index: int = self.indexFromItem(self.selectedItems()[0]).row()
                # when first parent item is selected go to last parent item
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
                # when the last parent item is selected go to first parent
                if (self.selectedItems()[0].childCount() and
                    not self.selectedItems()[0].isExpanded() and
                    item_index == parent_item_count-1):
                        # select first item
                        self.setCurrentItem(self.topLevelItem(0))
                        return
                # when last child item ist seleced go to first parent
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
            items_to_collapse: list[TreeWidgetItem] = []
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
        """Add parent item, to QTreeWidget with user inputs"""
        parent_item: TreeWidgetItem = TreeWidgetItem(dict(audiobook_key=audiobook_key,
                                                          parent=self))
        parent_item.setFlags(parent_item.flags() & ~Qt.ItemIsDragEnabled)
        parent_item.add_user_inputs()
        parent_item.setSizeHint(0, QSize(100, 100))
        return parent_item

    def add_child_item(self, args: dict) -> None:
        """Add child item to parent item"""
        child_item: TreeWidgetItem = TreeWidgetItem(args)
        child_item.setFlags(child_item.flags() & ~Qt.ItemIsDropEnabled)
        args["parent"].addChild(child_item)
        child_item.set_text(args)

    def create_tree(self, audiobook_data: dict) -> None:
        """Populate QtreeWidget with parent and child items"""
        for e_audiobook in audiobook_data:
            # create parent item
            audiobook: TreeWidgetItem = self.add_parent_item(e_audiobook)
            # edit user inputs with audiobook_data infos
            for input in audiobook.user_inputs:
                if not input in audiobook_data[e_audiobook]:
                    continue
                input_widget: (TextField | BookCover |
                               Label | ExportOptions | ToggleButton) = audiobook.user_inputs[input]
                if isinstance(input_widget, ToggleButton):
                    input_widget.args.update({"state": True if audiobook_data[e_audiobook][input] else False})
                    input_widget.toggle_color()
                    input_widget.args.update({"function": self.parent_item_counter_update})
                elif isinstance(input_widget, BookCover):
                    if not audiobook_data[e_audiobook][input]:
                        continue
                    input_widget.cover.load(audiobook_data[e_audiobook][input])
                    input_widget.setPixmap(input_widget.cover.scaledToHeight(70, Qt.SmoothTransformation))
                    input_widget.show_buttons(True)
                elif isinstance(input_widget, TextField):
                    input_widget.setText(audiobook_data[e_audiobook][input])
                elif isinstance(input_widget, ExportOptions):
                    input_widget.setCurrentIndex(audiobook_data[e_audiobook][input])
                elif isinstance(input_widget, Label):
                    input_widget.setText(str(timedelta(seconds=audiobook_data[e_audiobook][input])))
            # add all files as children
            for eFile in audiobook_data[e_audiobook]["files"]:
                self.add_child_item(dict(parent=audiobook,
                                         file=eFile["file"],
                                         duration=eFile["duration"],
                                         audiobook_key=e_audiobook))
        self.parent_item_counter_update()

    def parent_item_counter_update(self) -> None:
        """Update header active parent items counter"""
        root_item: QTreeWidgetItem = self.invisibleRootItem()
        parent_item_count: int = root_item.childCount()
        if not parent_item_count:
            self.help_text.show()
            self.help_text.move(self.rect().center() - self.help_text.rect().center())
            self.setHeaderLabels(["Audiobook (0/0)", "Duration"])
        else:
            parent_item_active: int = len([root_item.child(i) for i in range(parent_item_count)
                                                              if root_item.child(i).user_inputs["export"].args["state"]])
            self.help_text.hide()
            self.setHeaderLabels([f"Audiobook ({parent_item_active}/{parent_item_count})", "Duration"])

    def parent_item_duration_update(self, data: dict) -> None:
        """Update all parent item durations"""
        root_item: QTreeWidgetItem = self.invisibleRootItem()
        for e_data in data.values():
            for parent_item_index in range(root_item.childCount()):
                parent_item: TreeWidgetItem = self.topLevelItem(parent_item_index)
                if e_data["title"] in parent_item.user_inputs["title"].text():
                    parent_item.user_inputs["duration"].setText(str(timedelta(seconds=e_data["duration"])))


class TreeWidgetItem(QTreeWidgetItem):
    """Costum QTreeWidgetItem
    args: parent = QWidget
          audiobook_key = audiobook key from json
    """
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setFlags(Qt.ItemIsEnabled |
                      Qt.ItemIsSelectable |
                      Qt.ItemIsDropEnabled |
                      Qt.ItemIsDragEnabled)
        # contains all user inputs
        self.user_inputs: dict = {}
        # contains parent and audiobook key
        self.args: dict = args

    def set_text(self, args: dict) -> None:
        """Set text for TreeWidgetItem childs
        args:
            file: str = filepath
            duration: int = seconds
        """
        self.setText(0, QFileInfo(args["file"]).fileName())
        self.setText(1, str(timedelta(seconds=round(args["duration"]))))

    def add_user_inputs(self) -> None:
        """Creates a prent TreeWidgetItem with user inputs"""
        self.args["parent"].addTopLevelItem(self)
        # qwidget sets scale and style for column 0 & 1
        column0_style: QWidget = QWidget()
        column0_style.setObjectName("c0")
        column0_style.setStyleSheet("QWidget#c0 {background-color: rgba(200, 200, 200, 0.2);\
                                                 border-top-left-radius: 10px;\
                                                 border-bottom-left-radius: 10px;\
                                                 margin: 5px 0px 5px 0px;}")
        self.args["parent"].setItemWidget(self, 0, column0_style)
        column1_style: QWidget = QWidget()
        column1_style.setObjectName("c1")
        column1_style.setStyleSheet("QWidget#c1 {background-color: rgba(200, 200, 200, 0.2);\
                                                 border-top-right-radius: 10px;\
                                                 border-bottom-right-radius: 10px;\
                                                 margin: 5px 5px 5px 0px;}")
        self.args["parent"].setItemWidget(self, 1, column1_style)
        # audiobook user input editing widgets
        activate_export: ToggleButton = ToggleButton(dict(name="",
                                                          parent=column0_style,
                                                          geometry=[0, 0, 20, 100],
                                                          tip="Activate audiobook for export",
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
                                                   tip="Apply author presets",
                                                   action="author_preset",
                                                   user_inputs=dict()))
        book_quality: ExportOptions = ExportOptions(dict(options=Audiobook().quality_presets,
                                                         parent=column0_style,
                                                         geometry=[110, 55, 270, 25],
                                                         audiobook_key=self.args["audiobook_key"]))
        book_export: TextField = TextField(dict(name="Destination",
                                                tip="Export destination",
                                                parent=column0_style,
                                                geometry=[390, 55, 270, 25],
                                                audiobook_key=self.args["audiobook_key"]))
        file_browser: PushButton = PushButton(dict(name="\N{LOWER SEVEN EIGHTHS BLOCK}",
                                                   parent=column0_style,
                                                   geometry=[665, 53, 25, 30],
                                                   tip="Open file browser",
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
        # button needs ability to edit all user inputs
        book_presets.args.update({"user_inputs": self.user_inputs})


class PushButton(QPushButton):
    """Costum QPushButton
    args: parent = QWidget
          geometry = [x, y, w, h]
          fixed_size = [w, h]
          fixed_width = int in pixel
          fixed_height = int in pixel
          name = displayed text
          tip = displayed tooltip
          action = empty (no action applied), or function
    """
    def __init__(self, args: dict) -> None:
        super().__init__()
        if "parent" in args:
            self.setParent(args["parent"])
        self.setVisible(True)
        if "geometry" in args:
            self.setGeometry(*args["geometry"])
        if "fixed_size" in args:
            self.setFixedSize(*args["fixed_size"])
        if "fixed_width" in args:
            self.setFixedWidth(args["fixed_width"])
        if "fixed_height" in args:
            self.setFixedHeight(args["fixed_height"])
        self.setText(args["name"] if len(args["name"]) <= 35 else f"{args['name'][:30]}…")
        self.setToolTip(args["tip"])
        self.args: dict = args
        self.popMenu: QMenu
        # Signals
        if isinstance(args["action"], str):
            if args["action"] == "file_dialog":
                args.update({"action": self.file_dialog})
            elif args["action"] == "author_preset":
                self.setStyleSheet("QPushButton::menu-indicator {width: 0px;}")
                args.update({"action": self.empty})
                self.author_menu: PresetMenu = PresetMenu(self.args,)
                self.setMenu(self.author_menu)
            elif args["action"] == "export":
                 args.update({"action": self.export})
            else:
                args.update({"action": self.empty})
        self.clicked.connect(args["action"])

    def empty(self) -> None:
        """Empty signal function to avoid errors"""
        pass

    def export(self) -> None:
        """Export all Audiobooks"""
        audiobook: Audiobook = Audiobook()
        # open export dialog
        dialog: Dialog = Dialog(self.args["parent"]).export_ui()
        # connect export signals to dialog
        audiobook.signals.progress_range.connect(lambda: dialog.progressbar.setRange(0, audiobook.progress_range))
        audiobook.signals.progress_value.connect(lambda: dialog.progressbar.setValue(audiobook.progress_value))
        audiobook.signals.export_file.connect(lambda: dialog.text.appendPlainText(audiobook.export_file))
        audiobook.signals.unlock_ui.connect(lambda: dialog.buttonbox.setEnabled(audiobook.unlock_ui))
        # export function
        audiobook.export()

    def file_dialog(self) -> None:
        """Show a system file dialog and set user input to select path"""
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
    """Costum QMenu
    args: user_inputs = dictionary with user inputs
    """
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.args: dict = args
        self.aboutToShow.connect(self.create_author_preset_menu)

    def create_author_preset_menu(self) -> None:
        """Create preset item menu"""
        self.clear()
        self.addAction("Save", self.save_author_preset)
        self.addSeparator()
        # get presets from json
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
    """Costum QWidgetAction
    args: parent = QWidget
          name = displayed text
          user_inputs = dictionary with user inputs
    """
    def __init__(self, args: dict) -> None:
        super().__init__(args["parent"])
        self.container: QWidget = QWidget()
        self.preset_button: PushButton = PushButton(dict(name=args["name"],
                                                         fixed_size=[200, 20],
                                                         tip="Apply preset",
                                                         action=self.apply_author_preset))
        self.delete_button: PushButton = PushButton(dict(name="\N{HEAVY MULTIPLICATION X}",
                                                         fixed_size=[20, 20],
                                                         tip="Delete preset",
                                                         action=self.delete_author_preset))
        self.container.setStyleSheet("QPushButton {border: none;\
                                                   text-align: left;}\
                                      QPushButton:hover {color: #ffffff;\
                                                         background-color: #568dff;}")
        self.delete_button.setStyleSheet("QPushButton {text-align: center}")
        self.grid_layout: GridLayout = GridLayout(dict(parent=self.container,
                                                       margins=[18, 3, 5, 3],
                                                       spacing=3))
        self.grid_layout.addWidget(self.preset_button, 0, 0)
        self.grid_layout.addWidget(self.delete_button, 0, 1)
        self.setDefaultWidget(self.container)
        self.args: dict = args

    def apply_author_preset(self) -> None:
        """Apply preset to user inputs"""
        data: dict = Preset().read_data()
        self.args["user_inputs"]["author"].setText(self.args["name"])
        for key, value in data[self.args["name"]].items():
            widget: TextField | ExportOptions = self.args["user_inputs"][key]
            if isinstance(widget, TextField):
                widget.setText(value)
            elif isinstance(widget, ExportOptions):
                    widget.setCurrentIndex(value)

    def delete_author_preset(self) -> None:
        """Delete preset from json and QMenu"""
        Preset().delete_data(self.args["name"])
        self.deleteLater()


class ToggleButton(QPushButton):
    """Costum Toggle QPushButton
    args: parent = QWidget
          geometry = [x, y, w, h]
          name = displayed text
          audiobook_key = audiobook key from json
          state = toggle state of button
          function = function to call
    """
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setVisible(True)
        self.setGeometry(*args["geometry"])
        self.setText(args["name"])
        self.setStyleSheet("QPushButton {background-color: #439871;\
                                         border-top-left-radius: 10px;\
                                         border-bottom-left-radius: 10px;\
                                         margin: 5px 5px 5px 0px;}\
                            QPushButton:hover {background-color: #43be71;}")
        self.setToolTip(args["tip"])
        self.args: dict = args
        self.args.update({"state": True,
                          "function": None})
        self.colors: dict ={True: ["#439871", "#43be71"],
                            False: ["#c03d43", "#ff3d43"]}
        # Signals
        self.clicked.connect(self.toggle)

    def toggle_color(self) -> None:
        """Change color of button with given color"""
        toggle: list(bool, bool) = [self.args["state"], False if self.args["state"] else True]
        self.setStyleSheet(self.styleSheet().replace(self.colors[toggle[1]][0], self.colors[toggle[0]][0]))
        self.setStyleSheet(self.styleSheet().replace(self.colors[toggle[1]][1], self.colors[toggle[0]][1]))


    def toggle(self) -> None:
        """Update toggle state of button, change color, json and audiobook counter"""
        data: dict = Audiobook().read_data()
        audiobook_index: str = self.args["audiobook_key"]
        toggle_state: bool = data[audiobook_index]["export"]
        data[audiobook_index].update({"export": False if toggle_state else True})
        self.args["state"] = False if toggle_state else True
        self.toggle_color()
        self.args["function"]()
        Audiobook().save_data(data)


class Label(QLabel):
    """Costum QLabel
    args: parent = QWidget
          geometry = [x, y, w, h]
          text = displayed text
    """
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setVisible(True)
        self.setGeometry(*args["geometry"])
        self.setText(args["text"])


class BookCover(QLabel):
    """Costum QLabel to display artwork
    args: parent = QWidget
          audiobook_key = audiobook key from json
    """
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
                            PushButton {background-color: #c03d43;\
                                        color: white;\
                                        font-weight: bold;\
                                        border-radius: 10px;}\
                            PushButton:hover {background-color: #ff3d43;}")
        self.setAcceptDrops(True)
        self.cover: QPixmap = QPixmap()
        # buttons are visible when cover image is displayed
        self.delete_button: PushButton = PushButton(dict(parent=self,
                                                         geometry=[60, 0, 20, 20],
                                                         name="\N{HEAVY MULTIPLICATION X}",
                                                         tip="Delete cover",
                                                         action=self.delete_cover))
        self.delete_button.setVisible(False)
        # resize button is visible when cover image is not 1:1
        self.resize_button: PushButton = PushButton(dict(parent=self,
                                                         geometry=[60, 60, 20, 20],
                                                         name="\N{WARNING SIGN}",
                                                         tip="Resize cover 1:1",
                                                         action=self.resize_cover))
        self.resize_button.setVisible(False)
        self.args: dict = args

    def show_buttons(self, state: bool) -> None:
        """Set button visibility"""
        self.delete_button.setVisible(state)
        if not self.cover.isNull():
            state = True if self.cover.width() % self.cover.height() else False
        self.resize_button.setVisible(state)

    def delete_cover(self) -> None:
        """Delete active cover image"""
        Audiobook().delete_data(dict(cover="Delete",
                                     audiobook_key=self.args["audiobook_key"]))
        self.cover = QPixmap()
        self.show_buttons(False)
        self.setText(self.cover_text)

    def resize_cover(self) -> None:
        """Squares 1:1 cover image"""
        path: str = Audiobook().resize_cover(self.args["audiobook_key"])
        self.cover.load(path)
        self.setPixmap(self.cover.scaledToHeight(70, Qt.SmoothTransformation))
        self.show_buttons(True)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        """Drop cover image into widget"""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path: str = url.path()
                format: str = QFileInfo(url.path()).suffix()
                if not format in QImageWriter.supportedImageFormats():
                    Dialog(self.args["parent"]).log_ui(f"\"{format.upper()}\"\
                                                         is not a supported file format.\n\n{path}")
                    continue
                self.cover.load(path)
                self.setPixmap(self.cover.scaledToHeight(70, Qt.SmoothTransformation))
                event.acceptProposedAction()
                audiobook_index: str = self.args["audiobook_key"]
                data: dict = Audiobook().read_data()
                data[audiobook_index].update({"cover": path})
                self.show_buttons(True)
                Audiobook().save_data(data)
        else:
            super().dropEvent(event)


class TextField(QLineEdit):
    """Costum QLineEdit
    args: parent = QWidget
          geometry = [x, y, w, h]
          name = displayed text
          tip = displayed tooltip
          audiobook_key = audiobook key from json
    """
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setVisible(True)
        self.setGeometry(*args["geometry"])
        self.setPlaceholderText(args["name"])
        self.setToolTip(args["tip"])
        self.setStyleSheet("QLineEdit {border-radius: 5px;\
                                       border: 1px solid grey;\
                                       background-color: transparent;}\
                            QLineEdit:focus {border: 2px solid #568dff;}")
        self.args: dict = args
        # Signals
        self.textChanged.connect(self.text_edited)

    def text_edited(self) -> None:
        """User is editing textfields"""
        data: dict = Audiobook().read_data()
        audiobook_index: str = self.args["audiobook_key"]
        audiobook_input: str = self.args["name"].lower()
        data[audiobook_index].update({audiobook_input: self.text()})
        Audiobook().save_data(data)


class ExportOptions(QComboBox):
    """Custom QComboBox dropdown menu
    args: parent = QWidget
          geometry = [x, y, w, h]
          tip = displayed tooltip
          audiobook_key = audiobook key from json
          options = list of quality options
    """
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setParent(args["parent"])
        self.setVisible(True)
        self.setGeometry(*args["geometry"])
        self.addItems(args["options"])
        self.setToolTip("Change export quality")
        self.setStyleSheet("QComboBox {border-radius: 5px;\
                                       border: 1px solid grey;\
                                       background-color: transparent;\
                                       selection-background-color: #568dff;}")
        self.args: dict = args
        # Signals
        self.currentIndexChanged.connect(self.index_changed)

    def index_changed(self) -> None:
        """Update json when index is changed"""
        audiobook_index: str = self.args["audiobook_key"]
        data: dict = Audiobook().read_data()
        data[audiobook_index].update({"quality": self.currentIndex()})
        Audiobook().save_data(data)


class Dialog(QDialog):
    """Costum QDialog window"""
    def __init__(self, parent: QWidget) -> None:
        super().__init__()
        self.setParent(parent)
        self.buttonbox: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Close)
        self.buttonbox.rejected.connect(self.reject)
        self.text: QPlainTextEdit = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.grid_layout: GridLayout = GridLayout(dict(parent=self,
                                                       margins=[10, 10, 10, 10],
                                                       spacing=10))

    def log_ui(self, msg: str) -> Self:
        """Warning and error dialog"""
        self.setWindowTitle("Warning Message")
        self.setFixedSize(400, 200)
        self.text.appendPlainText(msg)
        self.grid_layout.addWidget(self.text, 0, 0)
        self.grid_layout.addWidget(self.buttonbox, 1, 0)
        self.open()
        return self

    def export_ui(self) -> Self:
        """Export dialog"""
        self.setWindowTitle("Export Audiobooks")
        self.setFixedSize(700, 400)
        self.buttonbox.setEnabled(False)
        self.progressbar: QProgressBar = QProgressBar()
        self.grid_layout.addWidget(self.progressbar, 0, 0)
        self.grid_layout.addWidget(self.text, 1, 0)
        self.grid_layout.addWidget(self.buttonbox, 2, 0)
        self.open()
        return self

    def about_ui(self, args: dict) -> Self:
        """App About dialog"""
        self.setStyleSheet("QLabel {color: grey;\
                                    font-family: Arial;\
                                    font-size: 12px;\
                                    font-weight: light;}")
        logo = QLabel()
        logo.setPixmap(QPixmap(QDir.currentPath()+"/AudiobookEncoder/icons/logo.png").scaledToWidth(400, Qt.SmoothTransformation))
        version = QLabel(f"<b>Version {args['version']}</b>")
        copyright = QLabel(f"<center>{args['copyright']}<br>\
                             <a href=\"mailto:{args['email']}\">{args['author']}</a></center>")
        copyright.linkActivated.connect(lambda: QDesktopServices().openUrl(QUrl(args["email"])))
        license = QLabel(f"<center><b>License</b><br>{args['license'][0]}<br>{args['license'][1]}</center>")
        sub_credits = QLabel("<center><b>Additional Credits</b>")
        python = QLabel("<center><a href=\"https://www.python.org\">Python</a></center>")
        python.linkActivated.connect(lambda: QDesktopServices().openUrl(QUrl("https://www.python.org")))
        pyside = QLabel("<center><a href=\"https://www.qt.io/qt-for-python\">PySide 6</a></center>")
        pyside.linkActivated.connect(lambda: QDesktopServices().openUrl(QUrl("https://www.qt.io/qt-for-python")))
        mutagen = QLabel("<center><a href=\"https://mutagen.readthedocs.io\">Mutagen</a></center>")
        mutagen.linkActivated.connect(lambda: QDesktopServices().openUrl(QUrl("https://mutagen.readthedocs.io")))
        abbinder = QLabel("<center><a href=\"https://github.com/gonzoua/AudiobookBinder\">Abbinder</a></center>")
        abbinder.linkActivated.connect(lambda: QDesktopServices().openUrl(QUrl("https://github.com/gonzoua/AudiobookBinder")))
        about: list = [version, copyright, license, sub_credits, python, pyside, mutagen, abbinder]
        # add to grid layout
        self.grid_layout.addWidget(logo, 0, 0, Qt.AlignCenter)
        for i, e in enumerate(about, 2):
            self.grid_layout.addWidget(e, i, 0, Qt.AlignCenter)
        self.grid_layout.addWidget(self.buttonbox, len(about)+2, 0)
        self.open()
        return self

    def keyPressEvent(self, event) -> None:
        if self.buttonbox.isEnabled():
            if event.key() == Qt.Key_Escape:
                self.close()

class GridLayout(QGridLayout):
    """Costum QGridLayout
    args: parent = QWidget
          margins = [l, t, r, b]
          spacing = int pixel
    """
    def __init__(self, args: dict) -> None:
        super().__init__()
        self.setContentsMargins(*args["margins"])
        self.setSpacing(args["spacing"])
        args["parent"].setLayout(self)