import re
from typing import Final, List, Optional, Tuple

import minecraft_data_api as mda
from mcdreforged import new_thread, CommandSource, PlayerCommandSource

from .death_data import DeathData, DeathLocation
from .execute_manager import ExecuteManager


def get_location_from_player(player_name: str) -> Tuple[List, str]:
    pos: List = mda.get_player_info(player_name, "Pos")
    dim: str = mda.get_player_info(player_name, "Dimension")
    return pos, dim


@new_thread(f"YatAnotherDeathBack: check_death")
def check_death(scoreboard_name: str, player_name: str, exec_mgr: ExecuteManager):
    if not player_name or not scoreboard_name:
        return
    query_command: Final[list[str]] = [
        "scoreboard",
        "players",
        "get",
        player_name,
        scoreboard_name
    ]
    output_regex: Final[re.Pattern] = re.compile(
        rf"{player_name} has (?P<score>-?\d+) \[{scoreboard_name}]$"
    )

    response: Optional[str] = exec_mgr.run(query_command, output_regex, timeout=.3)
    if not response:
        return
    match: Optional[re.Match] = output_regex.match(response)
    if not match:
        return
    score: int = int(match.group("score"))
    death_data: DeathData = DeathData.get_death_data_by_player_name(player_name)
    if score != death_data.death_score:
        pos, dim = get_location_from_player(player_name)
        death_data.death_score = score
        death_data.death_locations.insert(0, DeathLocation(
            pos[0], pos[1], pos[2], dim
        ))
        death_data.save(player_name)
        death_data.death_locations = death_data.death_locations[:3]
        exec_mgr.server.execute(
            f"tellraw {player_name} \"死亡位置 §e[{round(pos[0], 2)}, {round(pos[1], 2)}, {round(pos[2], 2)} ({dim})] "
            f"§r大概是记录了，使用 §l!b §r飞雷神。\"",
            encoding='UTF-8'
        )


def do_death_back(command_src: CommandSource):
    if not isinstance(command_src, PlayerCommandSource):
        return
    player_name = command_src.player
    death_data: DeathData = DeathData.get_death_data_by_player_name(player_name)
    if death_data.death_locations:
        location: DeathLocation = death_data.death_locations.pop(0)
        command_src.get_server().execute(
            f"execute in {location.dim} run tp {player_name} {location.x} {location.y} {location.z}"
        )
        death_data.save(player_name)
        command_src.get_server().execute(
            f"tellraw {player_name} \"让我们重新战斗吧！{player_name}！\"",
            encoding='UTF-8'
        )
    else:
        command_src.get_server().execute(
            f"tellraw {player_name} \"§4未找到记录，可能是我炸了您也就这么炸了，万分抱歉。\"",
            encoding='UTF-8'
        )
