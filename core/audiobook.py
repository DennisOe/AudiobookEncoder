# holds all scripts for editing audiobooks
# TODO: getFiles
# TODO: getFileDuration
# TODO: checkFiles
# TODO: getAudiobookDuration
# TODO: splitFiles in chunks of 12h  or 13h?
# TODO: expotAudiobook
# TODO: postExport -> meta tags, etc...
# TODO: play file
# TODO: saveDragJson
# TODO: createNewJason
# TODO: readAudiobook
# TODO: writeAudiobook
# TODO: deleteAudiobook
# TODO: deleteFile
# TODO: orderFile
# TODO: deleteCover
# TODO: readOptions
# TODO: writeOptions
# TODO: readPreset
# TODO: writePreset
# TODO: deletePreset
# TODO: Qtfaststart?

import mutagen
from mutagen.mp4 import MP4, MP4Cover 
from jsonio  import JsonIO

class Audiobook(JsonIO):
    def __init__(self):
        self.path = ""
        self.files: list[str]

    def audiobook_default_data(self) -> dict:
        data = {"name":
                    {"title": "",
                     "author": "",
                     "genre": "Audiobook",
                     "cover": "",
                     "duration": "",
                     "destination": "",
                     "quality": 0,
                     "files": [],
                     "export": True,
                    }
                }
        return data
    
    def append_data(self, data: dict, new_data: dict) -> dict:
        data.update(new_data)
        return data
    
    def delete_data(self, data: dict) -> dict:
        data.pop(data["title"], None)
        return data

    def update_data(self, data: dict, new_data: dict) -> dict:
        # TODO: update dict
        return data

    def add_files(self, files: list[str]) -> list[str]:
        for e_file in files:
            self.files.append(dict(file=e_file,
                                   duration="duration"))

    def save(self, data: dict) -> None:
        self.write(data, self.path)

    def get_meta_data(self, path: str) -> dict:
        audio_file = mutagen.File(path)
        title = " ".join(audio_file["TALB"].text) # album
        author = " ".join(audio_file["TPE1"].text) # artist
        duration = audio_file.info.length
        return dict(title=title, author=author, duration=duration)

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


        


