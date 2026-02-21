import time
from collections import defaultdict
from threading import Lock, Thread
from typing import Optional, Final, Any, DefaultDict, Set

from mcdreforged import PluginServerInterface, Info, Literal
from online_player_api import get_player_list

from .config import Config
from .constant import PLUGIN_FOLDER_NAME, DEATH_DATA_FOLDER_NAME
from .death_back import check_death, do_death_back
from .execute_manager import ExecuteManager
from .util import create_if_not_exist, backup_if_exist

# Why python doesn't have lazyinit
exec_mgr: Optional[ExecuteManager] = None
config: Optional[Any] = None

# Locks
_player_locks: DefaultDict[str, Lock] = defaultdict(Lock)
_recently_processed: Set[str] = set()
_recently_lock: Lock = Lock()


def _remove_and_recreate_scoreboard(server: PluginServerInterface) -> None:
    global config
    scoreboard_name: Final[str] = config.scoreboard_name
    server.execute(f"scoreboard objectives remove {scoreboard_name}")
    server.execute(f"scoreboard objectives add {scoreboard_name} deathCount")


def on_load(server: PluginServerInterface, _) -> None:
    global config, exec_mgr
    config = server.load_config_simple(target_class=Config, failure_policy='raise')
    exec_mgr = ExecuteManager(server)
    create_if_not_exist(PLUGIN_FOLDER_NAME)
    backup_if_exist(f"{PLUGIN_FOLDER_NAME}/{DEATH_DATA_FOLDER_NAME}", PLUGIN_FOLDER_NAME)
    for command in config.back_commands:
        server.register_command(
            Literal(command).runs(
                lambda command_src: do_death_back(command_src)
            )
        )
    _remove_and_recreate_scoreboard(server)


def on_server_startup(server: PluginServerInterface) -> None:
    _remove_and_recreate_scoreboard(server)


def on_info(_: PluginServerInterface, info: Info) -> None:
    if info.is_player:
        return
    global config, exec_mgr
    exec_mgr.on_info(info)
    for keyword in config.blacklisted_keywords:
        if keyword in info.raw_content:
            return
    if config.scoreboard_name in info.raw_content:
        return
    for player in get_player_list():
        if player not in info.raw_content:
            continue
        with _recently_lock:
            if player in _recently_processed:
                return
            _recently_processed.add(player)
        lock: Lock = _player_locks[player]
        if not lock.acquire(blocking=False):
            with _recently_lock:
                _recently_processed.discard(player)
            return
        try:
            check_death(config.scoreboard_name, player, exec_mgr)
        finally:
            lock.release()

            def remove_later(p: str) -> None:
                time.sleep(.1)
                with _recently_lock:
                    _recently_processed.discard(p)

            Thread(target=remove_later, args=(player,), daemon=True).start()
        break
