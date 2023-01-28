import time, random, os
from mutagen.easymp4 import EasyMP4
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from multiprocessing.pool import ThreadPool
from subprocess import Popen, PIPE, STDOUT
from threading import Thread
from PySide6.QtCore import (QUrl, QSize, QFileInfo, QDirIterator, QStandardPaths,
                            QThreadPool, Signal, QObject)
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from jsonio  import JsonIO


class Audiobook():
    """Edit data, audiobook files and meta data"""
    def __init__(self) -> None:
        super().__init__()
        self.audiobook_json_path: str = os.path.dirname(os.path.realpath(__file__)) + "/audiobooks.json"
        self.abbinder_path: str = os.path.dirname(os.path.realpath(__file__)) + "/abbinder"
        self.desktop_path: str = QStandardPaths.standardLocations(QStandardPaths.DesktopLocation)[0]
        self.quality_presets: list[str] = ["96 KBps, Mono, 44100",
                                           "96 KBps, Stereo, 48000",
                                           "128 KBps, Stereo, 48000",
                                           "256 KBps, Stereo, 48000",
                                           "320 KBps, Stereo, 48000"]
        self.data: dict = {"audiobook_index": {"title": "",
                                               "author": "",
                                               "genre": "Audiobook",
                                               "cover": "",
                                               "tracknumber": [1, 1],
                                               "duration": 0,
                                               "destination": self.desktop_path,
                                               "quality": 2,
                                               "files": [],
                                               "export": True,}}
        self.split_duration: dict[str, int] = {"24h": 86400,
                                               "20h": 72000,
                                               "12h": 43200,
                                               "10h": 36000}
        self.data_export: dict = {}
        # export signal attributes
        self.signals: CostumSignals = CostumSignals()
        self._progress_range: int = 0
        self._progress_value: int = 0
        self._export_file: str = ""
        self._unlock_ui: bool = False

    @property
    def export_file(self) -> str:
        return self._export_file

    @export_file.setter
    def export_file(self, file: str) -> None:
        self._export_file = file
        self.signals.export_file.emit(file)

    @property
    def progress_range(self) -> int:
        return self._progress_range

    @progress_range.setter
    def progress_range(self, p_range: int) -> None:
        self._progress_range = p_range
        self.signals.progress_range.emit(p_range)

    @property
    def progress_value(self) -> int:
        return self._progress_value

    @progress_value.setter
    def progress_value(self, value: int) -> None:
        self._progress_value = value
        self.signals.progress_value.emit(value)

    @property
    def unlock_ui(self) -> bool:
        return self._unlock_ui

    @unlock_ui.setter
    def unlock_ui(self, lock: bool) -> None:
        self._unlock_ui = lock
        self.signals.unlock_ui.emit(lock)

    def save_data(self, data: dict) -> dict:
        """Save user added data to json"""
        JsonIO.write(data, self.audiobook_json_path)
        return data

    def read_data(self) -> dict:
        """Read data from json"""
        return JsonIO.read(self.audiobook_json_path)

    def delete_data(self, data: dict) -> dict:
        """Delete data from json"""
        json_data: dict = JsonIO.read(self.audiobook_json_path)
        if "files" in data:
            # delete file
            for e_file in data["files"]:
                if not e_file["audiobook_key"] in json_data:
                    continue
                for e_json_file in json_data[e_file["audiobook_key"]]["files"]:
                    if not e_file["file"] in e_json_file["file"]:
                        continue
                    json_data[e_file["audiobook_key"]]["duration"] -= e_json_file["duration"]
                    json_data[e_file["audiobook_key"]]["files"].remove(e_json_file)
        elif "cover" in data:
            json_data[data["audiobook_key"]].update({"cover": ""})
        else:
            # delete audiobook
            for e_key in data["audiobook_keys"]:
                json_data.pop(e_key, None)
        self.save_data(json_data)
        return json_data

    def get_data(self, paths: list[QUrl]) -> dict:
        """Collects files from list, creates a dict and saves it to json"""
        files: list [str] = []
        json_data: dict = self.read_data()
        # collect and sort all files
        for each_path in paths:
            # folders
            if QFileInfo(each_path.path()).isDir():
                dir: QDirIterator = QDirIterator(each_path.path(), ["*.mp3"],
                                                 flags=QDirIterator.Subdirectories)
                while dir.hasNext():
                    file: str = dir.next()
                    files.append(file)
            else:
                # files
                if not each_path.path().lower().endswith(".mp3"):
                    continue
                files.append(each_path.path())
        files.sort()
        if not files:
            return {}
        # add meta data to json
        for each_file in files:
            meta_data: dict = self.get_meta_data(each_file)
            if "audiobook_index" in self.data:
                index: str = f"audiobook_{len(json_data)}"
                self.data.update({index: self.data.pop("audiobook_index")})
                self.data[index].update({"title": meta_data["title"]})
                self.data[index].update({"author": meta_data["author"]})
                # cover
                meta_cover = self.get_meta_cover(each_file, index)
                if meta_cover:
                    self.data[index].update({"cover": meta_cover})
            self.data[index]["duration"] += meta_data["duration"]
            self.data[index]["files"].append(dict(file=each_file,
                                                  duration=meta_data["duration"]))
        # try to apply existing author preset
        preset: Preset = Preset().auto_apply_data(", ".join([meta_data["title"],
                                                             meta_data["author"]]))
        if preset:
            author: list[str] = list(preset.keys())[0]
            self.data[index].update({"author": author})
            for key, value in preset[author].items():
                self.data[index].update({key: value})
        json_data.update(self.data)
        self.save_data(json_data)
        return self.data

    def get_meta_data(self, path: str) -> dict:
        """Read ID3 tags from mp3
        title, author, duration
        """
        audio_file: MP3 = MP3(path)
        meta_data: dict = {}
        for key, e_tag in [["title", "TALB"], ["author", "TPE1"]]:
            if not e_tag in audio_file:
                meta_data.update({key: ""})
                continue
            meta_data.update({key: " ".join(audio_file[e_tag].text)})
        meta_data.update({"duration": round(audio_file.info.length)})
        return meta_data

    def get_meta_cover(self, path: str, audiobook_key: str) -> str:
        """Extract and save ID3 cover from mp3"""
        audio_file: MP3 = MP3(path)
        cover_key: list[str] = [key for key in audio_file if "APIC:" in key.upper()]
        if not cover_key:
            return ""
        tag_cover: bytes = audio_file[cover_key[0]].data
        cover: QImage = QImage()
        cover.loadFromData(tag_cover)
        export_path: str = QFileInfo(path).path() + f"/{audiobook_key}_COVER.png"
        cover.save(export_path)
        return export_path

    def resize_cover(self, audiobook_key: str) -> str:
        """Squares cover"""
        data: dict = self.read_data()
        path: str = data[audiobook_key]["cover"]
        cover: QImage = QImage()
        cover.load(path)
        if cover.width() > cover.height():
            size: QSize = QSize(cover.width(), cover.width())
        else:
            size: QSize = QSize(cover.height(), cover.height())
        cover = cover.scaled(size)
        cover.save(path)
        return path

    def set_meta_data(self, path: str,  data: dict) -> None:
        """Save meta tags to m4b"""
        audio_file: EasyMP4 = EasyMP4(path)
        # set metadata
        audio_file["title"] = data["title"]
        audio_file["album"] = data["title"].split(" Part")[0]
        audio_file["artist"] = data["author"]
        audio_file["genre"] = data["genre"]
        audio_file["tracknumber"] = f"{data['tracknumber'][0]}/{data['tracknumber'][1]}"
        audio_file.save()
        # set cover image
        audio_file: MP4 = MP4(path)
        with open(data["cover"], "rb") as cover_file:
            audio_file.tags["covr"] = [MP4Cover(cover_file.read(), MP4Cover.FORMAT_PNG)]
            audio_file.save()

    def split_audiobooks(self) -> None:
        """Split audiobooks into XXh parts"""
        json_data: dict = self.read_data()
        for e_key, e_data in json_data.items():
            if not e_data["export"]:
                continue
            audiobook: dict = {}
            files: list[list] = [[]]
            files_index: int = 0
            key_index: int = len(self.data_export)
            duration: int = 0
            # change audiobook_1 key if exists
            audiobook_key: str = f"{e_key[:-1]}{key_index}" if e_key in self.data_export else e_key
            # audiobook LESS then XXh
            if e_data["duration"] <= self.split_duration["24h"]:
                self.data_export.update({audiobook_key: e_data})
                continue
            # audiobook MORE then XXh
            # split files in parts
            for e_file in e_data["files"]:
                if sum([duration, e_file["duration"]]) <= self.split_duration["24h"]:
                    duration += e_file["duration"]
                    files[files_index].append(e_file)
                    continue
                duration = e_file["duration"]
                files_index += 1
                files.append([e_file])
            # create a new dict from file parts
            for part, e_file in enumerate(files, 1):
                audiobook_key = f"{e_key[:-1]}{key_index}"
                audiobook.update({audiobook_key: e_data.copy()})
                # new title with part in name
                audiobook[audiobook_key].update({"title": f"{e_data['title']} Part {part}"})
                # add tracknumbers to parts
                audiobook[audiobook_key].update({"tracknumber": [part, len(files)]})
                audiobook[audiobook_key].update({"files": e_file})
                # new duration
                part_duration: int = sum([f["duration"] for f in e_file])
                audiobook[audiobook_key].update({"duration": part_duration})
                key_index += 1
            self.data_export.update(audiobook)

    def export(self) -> None:
        """Export audiobook"""
        self.data_export.clear()
        self.split_audiobooks()
        if not self.data_export:
            self.unlock_ui = True
            self.export_file = "Nothing to export…\n"
            return
        self.unlock_ui = False
        self.progress_range = len(self.data_export)
        self.export_file = f"Start exporting {self.progress_range} file(s)…\n"
        # Extra thread to avoid ui freeze
        export_thread: Thread = Thread(target=self.export_pool)
        export_thread.start()

    def export_pool(self) -> None:
        """Multiprocessing depending on cpu cores"""
        with ThreadPool(QThreadPool().maxThreadCount()) as export_pool:
            export_pool.map(self.export_audiobook, self.data_export.values())
        self.export_file = "Done exporting…\n"
        self.unlock_ui = True

    def export_audiobook(self, data: dict) -> None:
        """Main export function"""
        time.sleep(random.uniform(0.01, 5.0))
        self.export_file = f"%  STARTED --> {data['title']}\n"
        export_file: str = f"{data['destination']}/{data['title']}.m4b"
        if not QFileInfo(data['destination']).exists():
            export_file = f"{self.desktop_path}/{data['title']}.m4b"
        files: str = [e["file"] for e in data['files']]
        bitrate, channels, sample_rate = self.quality_presets[data['quality']].split(", ")
        channels: str = "2" if "Stereo" in channels else "1" # Stereo, Mono
        abbinder_cmd: str = [self.abbinder_path, # executable path
                             "-sv",              # skip errors, print infos
                             "-b", bitrate,      # in KBps
                             "-r", sample_rate,  # (44100 default), 48000
                             "-c", channels,     # 1, (2 default)
                             "-E", "%N",         # chapter by file: %N -> numbered
                             export_file,        # export path
                             *files]             # source files
        process: Popen = Popen(abbinder_cmd, stdout=PIPE, stderr=STDOUT)
        _stdout, _stderr = process.communicate()
        self.set_meta_data(export_file, data)
        self.export_file = f"%  DONE --> {data['title']}\n"
        self.progress_value += 1


class Preset():
    """Edit preset data"""
    def __init__(self) -> None:
        self.preset_json_path: str = os.path.dirname(os.path.realpath(__file__)) + "/presets.json"
        self.desktop_path: str = QStandardPaths.standardLocations(QStandardPaths.DesktopLocation)[0]
        self.data: dict = {"author": {"destination": self.desktop_path,
                                      "quality": 1}}

    def save_data(self, data: dict) -> dict:
        """Save user added data to json"""
        JsonIO.write(data, self.preset_json_path)
        return data

    def read_data(self) -> dict:
        """Read data from json"""
        return JsonIO.read(self.preset_json_path)

    def delete_data(self, key: str) -> dict:
        """Delete data from json
        args: key = name of preset
        """
        json_data: dict = self.read_data()
        json_data.pop(key, None)
        self.save_data(json_data)
        return json_data

    def get_data(self, user_inputs: dict) -> dict:
        """Collect data from user inputs"""
        json_data: dict = self.read_data()
        self.data.update({user_inputs["author"]: self.data.pop("author")})
        for key, value in self.data[user_inputs["author"]].items():
            self.data[user_inputs["author"]].update({key: user_inputs[key]})
        json_data.update(self.data)
        self.save_data(json_data)
        return self.data

    def auto_apply_data(self, meta_data: str) -> dict:
        """Compares data keys with meta data to auto apply a preset"""
        json_data: dict = self.read_data()
        preset_key: list[str] = [e_key for e_key in json_data.keys() if e_key in meta_data]
        if not preset_key:
            return {}
        sorted(preset_key, key=len)
        # apply preset
        self.data.update({preset_key[0]: self.data.pop("author")})
        for key, value in json_data[preset_key[0]].items():
            self.data[preset_key[0]].update({key: value})
        return self.data


class AudioPlayer(QMediaPlayer):
    """Audioplayer plays audiofiles"""
    def __init__(self, parent) -> None:
        super().__init__()
        self.setParent(parent)
        self.audio_output: QAudioOutput = QAudioOutput(parent)
        self.setAudioOutput(self.audio_output)
        self.playing_state: bool = False

    def play_audio(self, path: str) -> None:
        """Start, stop and switch files"""
        if not self.validate_file(path):
            return
        if self.playbackState() == QMediaPlayer.StoppedState:
            self.setSource(QUrl.fromLocalFile(path))
            self.play()
            self.playing_state = True
        elif path not in self.source().path():
            # switch file without stopping
            self.setSource(QUrl.fromLocalFile(path))
            self.play()
            self.playing_state = True
        else:
            self.stop()
            self.playing_state = False

    def validate_file(self, path: str) -> bool:
        """Check for valid files (mp3, exists)"""
        if (not path.endswith(".mp3") or
           not QFileInfo(path).exists()):
            return False
        return True


class CostumSignals(QObject):
    """Costum signals for widgets to connect to"""
    export_file = Signal(str)
    progress_range = Signal(int)
    progress_value = Signal(int)
    unlock_ui = Signal(bool)