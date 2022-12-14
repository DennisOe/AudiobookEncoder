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

from jsonio  import JsonIO

class Audiobook(JsonIO):
    def __init__(self):
        self.path = ""

    def audiobook_default_data(self) -> dict:
        data = {"Audiobook":
                    {"title": "",
                     "author": "",
                     "genre": "",
                     "cover": "",
                     "length": "",
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

    def save(self, data: dict) -> None:
        self.write(data, self.path)
    


