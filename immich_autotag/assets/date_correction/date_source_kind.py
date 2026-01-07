from enum import Enum, auto


class DateSourceKind(Enum):
    IMMICH = auto()
    WHATSAPP_FILENAME = auto()
    WHATSAPP_PATH = auto()
    FILENAME = auto()
    EXIF = auto()
    OTHER = auto()

    def __str__(self):
        return self.name
