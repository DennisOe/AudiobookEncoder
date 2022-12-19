# holds all scripts for editing audiobooks
import mutagen
from mutagen.mp4 import MP4, MP4Cover 
from jsonio  import JsonIO
from PySide6 import QtCore

class Audiobook():
    def __init__(self):
        self.path: str = "AudiobookEncoder/core/audiobooks.json"
        self.files: list[str]
        self.data: dict = {"name": {"title": "",
                                    "author": "",
                                    "genre": "Audiobook",
                                    "cover": "",
                                    "duration": 0,
                                    "destination": "",
                                    "quality": 0,
                                    "files": [],
                                    "export": True,}}
    
    def save_data(self) -> dict:
        json_data = JsonIO().read(self.path)
        json_data.update(self.data)
        JsonIO().write(json_data, self.path)
        return json_data
    
    def delete_data(self, key: str) -> dict:
        json_data = JsonIO.read(self.path)
        json_data.pop(key, None)
        JsonIO().write(json_data, self.path)
        return json_data
    
    def get_data(self, paths: list[QtCore.QUrl]) -> dict:
        files: list = []
        for each_path in paths:
            if QtCore.QFileInfo(each_path.path()).isDir():
                    dir = QtCore.QDirIterator(each_path.path(), ["*.mp3"],
                                              flags=QtCore.QDirIterator.Subdirectories)
                    while dir.hasNext():
                        file = dir.next()
                        files.append(file)
            else:
                files.append(each_path.path())
        files.sort()
        for each_file in files:
            if not each_file.lower().endswith(".mp3"):
                continue
            meta_data = self.get_meta_data(each_file)                    
            if "name" in self.data:
                title = meta_data["title"]
                self.data[title] = self.data.pop("name")
                self.data[title]["title"] = meta_data["title"]
                self.data[title]["author"] = meta_data["author"]
            self.data[title]["duration"] += meta_data["duration"]
            self.data[title]["files"].append(dict(file=each_file,
                                                  duration=meta_data["duration"]))
        self.save_data()
        return self.data

    def get_meta_data(self, path: str) -> dict:
        audio_file = mutagen.File(path)
        title: str = ""
        author: str = ""
        meta_data = {}
        for key, e_tag in [["title", "TALB"], ["author", "TPE1"]]:
            if not e_tag in audio_file:
                meta_data.update({key: ""})
                continue
            meta_data.update({key: " ".join(audio_file[e_tag].text)})
        else:
            duration = round(audio_file.info.length)
            meta_data.update({"duration": duration})
        return meta_data

    def set_meta_data(self, path: str, tags: dict):
        audio_file = mutagen.File(path, easy=True)
        # set metadata
        audio_file["title"] = tags["title"]
        audio_file["album"] = tags["album"]
        audio_file["artist"] = tags["author"]
        audio_file["genre"] = tags["genre"]
        audio_file["tracknumber"] = tags["tracknumber"]
        audio_file.save()
        # set cover image
        audio_file = MP4(path)
        cover_file = open(tags["cover"], "rb").read()
        audio_file.tags["covr"] = [MP4Cover(cover_file, MP4Cover.FORMAT_PNG)]
        audio_file.save() 


        

#Audiobook().get_meta_data("/Users/dennisoesterle/Desktop/test.mp3")
