import json


class JsonIO:
    """This class edits all necessary custom user information."""
    @staticmethod
    def write(data: dict, path: str) -> bool:
        """Write json file."""
        with open(path, "w") as json_file:
            json.dump(data, json_file, indent=4)
        return True

    @staticmethod
    def read(path: str) -> dict:
        """Read json file."""
        with open(path) as json_file:
            data = json.load(json_file)
            return data
