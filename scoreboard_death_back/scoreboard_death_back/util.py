import shutil
import tarfile
from datetime import datetime
from pathlib import Path


def backup_if_exist(path: str, backup_dir: str) -> None:
    p = Path(path)
    if p.exists() and p.is_dir():
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"{p.name}_{timestamp}.tar.gz"
        backup_path = Path(backup_dir) / backup_name

        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(p, arcname=p.name)
        shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)


def create_if_not_exist(path: str) -> None:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
