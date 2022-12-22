# holds all scripts for editing audiobooks
import mutagen
from mutagen.mp4 import MP4, MP4Cover
from PySide6.QtCore import QUrl, QFileInfo, QDirIterator
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
        if keys["file"]:
            # delete file
            for e_file in json_data[keys["audiobook_key"]]["files"]:
                if keys["file"] in e_file["file"]:
                    json_data[keys["audiobook_key"]]["files"].remove(e_file)
        else:
            # delete audiobook
            json_data.pop(keys["audiobook_key"], None)     
        JsonIO().write(json_data, self.path)
        return json_data
    
    def get_data(self, paths: list[QUrl]) -> dict:
        files: list [str] = []
        audiobook_count: int = len(self.read_data())
        for each_path in paths:
            if QFileInfo(each_path.path()).isDir():
                dir: QDirIterator = QDirIterator(each_path.path(), ["*.mp3"],
                                                 flags=QDirIterator.Subdirectories)
                while dir.hasNext():
                    file: str = dir.next()
                    files.append(file)
            else:
                files.append(each_path.path())
        files.sort()
        for each_file in files:
            if not each_file.lower().endswith(".mp3"):
                continue
            meta_data: dict = self.get_meta_data(each_file)                    
            if "audiobook_index" in self.data:
                title: str = f"audiobook_{audiobook_count}"
                self.data[title] = self.data.pop("audiobook_index")
                self.data[title]["title"] = meta_data["title"]
                self.data[title]["author"] = meta_data["author"]
            self.data[title]["duration"] += meta_data["duration"]
            self.data[title]["files"].append(dict(file=each_file,
                                                  duration=meta_data["duration"]))
        self.save_data(self.data)
        return self.data

    def get_meta_data(self, path: str) -> dict:
        audio_file = mutagen.File(path)
        title: str = ""
        author: str = ""
        meta_data: dict = {}
        for key, e_tag in [["title", "TALB"], ["author", "TPE1"]]:
            if not e_tag in audio_file:
                meta_data.update({key: ""})
                continue
            meta_data.update({key: " ".join(audio_file[e_tag].text)})
        else:
            duration: float = round(audio_file.info.length)
            meta_data.update({"duration": duration})
        return meta_data

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


        

#Audiobook().get_meta_data("/Users/dennisoesterle/Desktop/test.mp3")
