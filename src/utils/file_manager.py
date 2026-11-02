from pathlib import Path


def ensure_storage(path: Path) -> None:
    (path / "pdf").mkdir(parents=True, exist_ok=True)
    (path / "epub").mkdir(parents=True, exist_ok=True)
