import mutagen
from mutagen.mp4 import MP4, MP4Cover
from multiprocessing import Pool
from subprocess import Popen, PIPE, STDOUT
from threading import Thread
from PySide6.QtCore import QUrl, QSize, QFileInfo, QDirIterator, QStandardPaths, QThreadPool
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from jsonio  import JsonIO


class Audiobook():
    """Edit data, audiobook files and meta data"""
    def __init__(self) -> None:
        self.audiobook_json_path: str = "AudiobookEncoder/core/audiobooks.json"
        self.abbinder_path: str = "AudiobookEncoder/core/abbinder"
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
            # delete file
            for e_file in json_data[keys["audiobook_key"]]["files"]:
                if keys["file"] in e_file["file"]:
                    json_data[keys["audiobook_key"]]["duration"] -= e_file["duration"]
                    json_data[keys["audiobook_key"]]["files"].remove(e_file)
        elif "cover" in keys:
            json_data[keys["audiobook_key"]].update({"cover": ""})
        else:
            # delete audiobook
            json_data.pop(keys["audiobook_key"], None)
        self.save_data(json_data)
        return json_data

    def get_data(self, paths: list[QUrl]) -> dict:
        """Collects files from list, creates a dict and saves it to json"""
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
                index: str = f"audiobook_{audiobook_count}"
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
        preset = Preset().auto_apply_data(", ".join([meta_data["title"],
                                                     meta_data["author"]]))
        if preset:
            author = list(preset.keys())[0]
            self.data[index].update({"author": author})
            for key, value in preset[author].items():
                self.data[index].update({key: value})
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

    def set_meta_data(self, path: str,  data: dict) -> None:
        """Save meta tags to m4b"""
        audio_file = mutagen.File(path, easy=True)
        # set metadata
        audio_file["title"] = data["title"]
        audio_file["album"] = data["title"]
        audio_file["artist"] = data["author"]
        audio_file["genre"] = data["genre"]
        audio_file["tracknumber"] = f"{data['tracknumber'][0]}/{data['tracknumber'][1]}"
        audio_file.save()
        # set cover image
        audio_file: MP4 = MP4(path)
        with open(data["cover"], "rb") as cover_file:
            audio_file.tags["covr"] = [MP4Cover(cover_file.read(), MP4Cover.FORMAT_PNG)]
            audio_file.save()

    def export(self):
        """Extra thread for export to aboid freeze"""
        export_thread: Thread = Thread(target=self.export_pool)
        export_thread.start()

    def export_pool(self):
        """Multiprocessing depending on cpu cores"""
        export_pool: Pool = Pool(QThreadPool().maxThreadCount())
        export_pool.map(self.export_audiobook, self.read_data().keys())
        export_pool.close()
        export_pool.join()

    def export_audiobook(self, audiobook_key):
        """Main export function"""
        json_data: dict = self.read_data()
        export_file: str = f"{json_data[audiobook_key]['destination']}/{json_data[audiobook_key]['title']}.m4b"
        files: str = [e["file"] for e in json_data[audiobook_key]['files']]
        # "-sv" = skip errors and go on with conversion, print some info on files being converted
        # "-b" = bitrate in KBps
        # "-r" = sample rate : 8000, 11025, 12000, 16000, 22050, 24000, 32000, (44100 default), 48000
        # "-c" = audio channels : 1, (2 default)
        # "-E" = each file chapter: "%t" title, "%N" number
        bitrate, channels, sample_rate = self.quality_presets[json_data[audiobook_key]['quality']].split(", ")
        channels: str = "2" if "Stereo" in channels else "1" # Mono
        abbinder_cmd: str = [self.abbinder_path, "-sv", "-b", bitrate, "-r", sample_rate, "-c", channels, "-E", "%N", export_file] + files
        process: Popen = Popen(abbinder_cmd, stdout=PIPE, stderr=STDOUT)
        _stdout, _stderr = process.communicate()
        self.set_meta_data(export_file, json_data[audiobook_key])


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
        self.data.update({user_inputs["author"]: self.data.pop("author")})
        for key, value in self.data[user_inputs["author"]].items():
            self.data[user_inputs["author"]].update({key: user_inputs[key]})
        json_data.update(self.data)
        self.save_data(json_data)
        return self.data

    def auto_apply_data(self, meta_data: str) -> dict:
        """Compares data keys with meta data to auto apply a preset"""
        json_data: dict = self.read_data()
        preset_key = [e_key for e_key in json_data.keys() if e_key in meta_data]
        if not preset_key:
            return {}
        sorted(preset_key, key=len)
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