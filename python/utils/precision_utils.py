from enum import IntEnum

class Precision(IntEnum):
    INSENSITIVE = 0
    COARSE      = 1
    LOW         = 2
    MEDIUM      = 3
    HIGH        = 4

    @classmethod
    def from_string(cls, s: str) -> "Precision":
        try:
            return cls[s.strip().upper()]
        except KeyError:
            raise ValueError(f"Invalid precision level: {s}")

    def __str__(self) -> str:
        return self.name.lower()
