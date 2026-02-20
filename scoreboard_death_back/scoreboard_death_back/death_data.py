import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List

from .constant import PLUGIN_FOLDER_NAME, DEATH_DATA_FOLDER_NAME


@dataclass
class DeathLocation:
    x: float
    y: float
    z: float
    dim: str

    def __post_init__(self) -> None:
        if not isinstance(self.dim, str):
            raise TypeError(f"dim must be str, got {type(self.dim)}")


@dataclass
class DeathData:
    death_score: int = 0
    death_locations: List[DeathLocation] = field(default_factory=list)

    @staticmethod
    def _get_path(player_name: str) -> Path:
        return Path(PLUGIN_FOLDER_NAME) / DEATH_DATA_FOLDER_NAME / f"{player_name}.json"

    @classmethod
    def get_death_data_by_player_name(cls, player_name: str) -> "DeathData":
        death_file = cls._get_path(player_name)

        if not death_file.exists():
            return cls()

        try:
            with death_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            locations: List[DeathLocation] = []

            for loc in data.get("death_locations", []):
                if not isinstance(loc, dict):
                    continue

                dim = loc.get("dim")
                if not isinstance(dim, str):
                    continue

                try:
                    locations.append(
                        DeathLocation(
                            x=float(loc["x"]),
                            y=float(loc["y"]),
                            z=float(loc["z"]),
                            dim=dim
                        )
                    )
                except (KeyError, TypeError, ValueError):
                    continue
            return cls(
                death_score=data.get("death_score", 0),
                death_locations=locations
            )
        except (json.JSONDecodeError, TypeError, KeyError):
            return cls()

    def save(self, player_name: str):
        death_file = self._get_path(player_name)
        death_file.parent.mkdir(parents=True, exist_ok=True)
        with death_file.open("w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=4, ensure_ascii=False)