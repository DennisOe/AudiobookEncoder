import mutagen
from mutagen.mp4 import MP4, MP4Cover
from PySide6.QtCore import QUrl, QSize, QFileInfo, QDirIterator
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from jsonio  import JsonIO


class Audiobook():
    def __init__(self):
        self.path: str = "AudiobookEncoder/core/audiobooks.json"
        self.data: dict = {"audiobook_index": {"title": "",
                                               "author": "",
                                               "genre": "Audiobook",
                                               "cover": "",
                                               "duration": 0,
                                               "destination": "",
                                               "quality": 0,
                                               "files": [],
                                               "export": True,}}

    def save_data(self, data: dict) -> dict:
        json_data: dict = JsonIO().read(self.path)
        json_data.update(data)
        JsonIO().write(json_data, self.path)
        return json_data

    def read_data(self) -> dict:
        return JsonIO.read(self.path)

    def delete_data(self, keys: dict[str, str]) -> dict:
        json_data: dict = JsonIO.read(self.path)
        if "file" in keys:
            if not keys["file"]:
                return
            # delete file
            for e_file in json_data[keys["audiobook_key"]]["files"]:
                if keys["file"] in e_file["file"]:
                    json_data[keys["audiobook_key"]]["files"].remove(e_file)
        elif "cover" in keys:
            json_data[keys["audiobook_key"]]["cover"] = ""
        else:
            # delete audiobook
            json_data.pop(keys["audiobook_key"], None)
        JsonIO().write(json_data, self.path)
        return json_data

    def get_data(self, paths: list[QUrl]) -> dict:
        files: list [str] = []
        audiobook_count: int = len(self.read_data())
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
                self.data[title] = self.data.pop("audiobook_index")
                self.data[title]["title"] = meta_data["title"]
                self.data[title]["author"] = meta_data["author"]
                # cover
                meta_cover = self.get_meta_cover(each_file, title)
                if meta_cover:
                    self.data[title]["cover"] = meta_cover
            self.data[title]["duration"] += meta_data["duration"]
            self.data[title]["files"].append(dict(file=each_file,
                                                  duration=meta_data["duration"]))
        self.save_data(self.data)
        return self.data

    def get_meta_data(self, path: str) -> dict:
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


class AudioPlayer(QMediaPlayer):
    def __init__(self, parent) -> None:
        super().__init__()
        self.setParent(parent)
        self.audio_output: QAudioOutput = QAudioOutput(parent)
        self.setAudioOutput(self.audio_output)

    def play_audio(self, path: str) -> None:
        if not self.validate_file(path):
            return
        if self.playbackState() == QMediaPlayer.StoppedState:
            self.setSource(QUrl.fromLocalFile(path))
            self.play()
        elif path not in self.source().path():
            # switch file without stopping
            self.setSource(QUrl.fromLocalFile(path))
            self.play()
        else:
            self.stop()

    def validate_file(self, path: str) -> bool:
        if (not path.endswith(".mp3") or
           not QFileInfo(path).exists()):
            return False
        return True