import uuid
from queue import Queue, Empty
from threading import RLock
from typing import Dict, Optional, Pattern, List

from mcdreforged import PluginServerInterface, Info


class ExecuteManager:
    class CommandTask:
        def __init__(self, output_regex: Pattern[str]):
            self.queue: Queue[str] = Queue()
            self.count: int = 0
            self.output_regex = output_regex

    def __init__(self, server: PluginServerInterface):
        self.server = server
        self.lock = RLock()
        self.tasks: Dict[uuid.UUID, ExecuteManager.CommandTask] = {}

    def run(self, command: List[str], output_regex: Pattern[str], timeout: float = None) -> Optional[str]:
        full_command = ' '.join(command)
        task_id = uuid.uuid4()
        task = self.CommandTask(output_regex)
        task.count += 1
        with self.lock:
            self.tasks[task_id] = task

        self.server.execute(full_command)

        try:
            result = task.queue.get(timeout=timeout)
            return result
        except Empty:
            self.server.logger.warning(f'Command "{full_command}" timed out')
            return None
        finally:
            with self.lock:
                task.count -= 1
                del self.tasks[task_id]

    def on_info(self, info: Info):
        with self.lock:
            for task in self.tasks.values():
                if _ := task.output_regex.match(info.content):
                    if task.count > 0:
                        task.queue.put(info.content)
