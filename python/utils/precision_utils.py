from enum import IntEnum

class Precision(IntEnum):
    INSENSITIVE = 0
    LOW         = 1
    MEDIUM      = 2
    HIGH        = 3

    @classmethod
    def from_string(cls, s: str) -> "Precision":
        try:
            return cls[s.strip().upper()]
        except KeyError:
            raise ValueError(f"Invalid precision level: {s}")

    def __str__(self) -> str:
        return self.name.lower()
