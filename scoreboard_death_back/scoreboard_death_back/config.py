from typing import List

from mcdreforged.api.all import Serializable


class Config(Serializable):
    back_commands: List[str] = [
        "!!back", "!b"
    ]
    scoreboard_name: str = "scoreboard_death_back_death_count"
    blacklisted_keywords: List[str] = [
        "has the following entity data",
        "has made the advancement",
        "joined the game",
        "logged in with entity id",
        "left the game"
    ]
