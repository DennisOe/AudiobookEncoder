import mutagen
from mutagen.mp4 import MP4, MP4Cover
from PySide6.QtCore import QUrl, QSize, QFileInfo, QDirIterator, QStandardPaths
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from jsonio  import JsonIO


class Audiobook():
    """Edit data, audiobook files and meta data"""
    def __init__(self) -> None:
        self.audiobook_json_path: str = "AudiobookEncoder/core/audiobooks.json"
        self.desktop_path: str = QStandardPaths.standardLocations(QStandardPaths.DesktopLocation)[0]
        self.quality_presets: list[str] = ["96 Kbps, Stereo, 48 kHz",
                                           "128 Kbps, Stereo, 48 kHz",
                                           "256 Kbps, Stereo, 48 kHz",
                                           "320 Kbps, Stereo, 48 kHz"]
        self.data: dict = {"audiobook_index": {"title": "",
                                               "author": "",
                                               "genre": "Audiobook",
                                               "cover": "",
                                               "duration": 0,
                                               "destination": self.desktop_path,
                                               "quality": 1,
                                               "files": [],
                                               "export": True,}}

    def save_data(self, data: dict) -> dict:
        """Save user added data to json"""
        JsonIO().write(data, self.audiobook_json_path)
        return data

    def read_data(self) -> dict:
        """Read data from json"""
        return JsonIO.read(self.audiobook_json_path)

    def delete_data(self, keys: dict[str, str]) -> dict:
        """Delete data from json"""
        json_data: dict = JsonIO.read(self.audiobook_json_path)
        if "file" in keys:
            if not keys["file"]:
                return
            # delete file
            for e_file in json_data[keys["audiobook_key"]]["files"]:
                if keys["file"] in e_file["file"]:
                    json_data[keys["audiobook_key"]]["files"].remove(e_file)
        elif "cover" in keys:
            json_data[keys["audiobook_key"]].update({"cover": ""})
        else:
            # delete audiobook
            json_data.pop(keys["audiobook_key"], None)
        self.save_data(json_data)
        return json_data

    def get_data(self, paths: list[QUrl]) -> dict:
        """Collects data from drag and drop event and saves it"""
        files: list [str] = []
        json_data: dict = self.read_data()
        audiobook_count: int = len(json_data)
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
                title: str = f"audiobook_{audiobook_count}"
                self.data.update({title: self.data.pop("audiobook_index")})
                self.data[title].update({"title": meta_data["title"]})
                self.data[title].update({"author": meta_data["author"]})
                # cover
                meta_cover = self.get_meta_cover(each_file, title)
                if meta_cover:
                    self.data[title].update({"cover": meta_cover})
            self.data[title]["duration"] += meta_data["duration"]
            self.data[title]["files"].append(dict(file=each_file,
                                                  duration=meta_data["duration"]))
        json_data.update(self.data)
        self.save_data(json_data)
        return self.data

    def get_meta_data(self, path: str) -> dict:
        """Read ID3 tags from mp3"""
        audio_file = mutagen.File(path)
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
        audio_file = mutagen.File(path)
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

    def set_meta_data(self, path: str, tags: dict) -> None:
        """Save meta tags to m4b"""
        audio_file = mutagen.File(path, easy=True) # TODO
        # set metadata
        audio_file["title"] = tags["title"]
        audio_file["album"] = tags["album"]
        audio_file["artist"] = tags["author"]
        audio_file["genre"] = tags["genre"]
        audio_file["tracknumber"] = tags["tracknumber"]
        audio_file.save()
        # set cover image
        audio_file: MP4 = MP4(path)
        cover_file = open(tags["cover"], "rb").read() # TODO
        audio_file.tags["covr"] = [MP4Cover(cover_file, MP4Cover.FORMAT_PNG)]
        audio_file.save()


class Preset():
    """Edit preset data"""
    def __init__(self) -> None:
        self.preset_json_path: str = "AudiobookEncoder/core/presets.json"
        self.desktop_path: str = QStandardPaths.standardLocations(QStandardPaths.DesktopLocation)[0]
        self.data: dict = {"author": {"destination": self.desktop_path,
                                      "quality": 1}}

    def save_data(self, data: dict) -> dict:
        """Save user added data to json"""
        JsonIO().write(data, self.preset_json_path)
        return data

    def read_data(self) -> dict:
        """Read data from json"""
        return JsonIO.read(self.preset_json_path)

    def delete_data(self, key: str) -> dict:
        """Delete data from json"""
        json_data: dict = self.read_data()
        json_data.pop(key, None)
        self.save_data(json_data)
        return json_data

    def get_data(self, user_inputs: dict) -> dict:
        """Collect data from user inputs"""
        json_data: dict = self.read_data()
        self.data[user_inputs["author"]] = self.data.pop("author")
        for key, value in self.data[user_inputs["author"]].items():
            self.data[user_inputs["author"]].update({key: user_inputs[key]})
        json_data.update(self.data)
        self.save_data(json_data)
        return self.data


class AudioPlayer(QMediaPlayer):
    """Audioplayer plays mp3s"""
    def __init__(self, parent) -> None:
        super().__init__()
        self.setParent(parent)
        self.audio_output: QAudioOutput = QAudioOutput(parent)
        self.setAudioOutput(self.audio_output)
        self.playing_state: bool = False

    def play_audio(self, path: str) -> None:
        """Start, stop and switch mp3s"""
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