from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs"
LEGACY_RUNTIME_DIR = ROOT_DIR / "legacy" / "runtime"
LEGACY_KNOWLEDGE_DIR = ROOT_DIR / "legacy" / "knowledge"
BACKEND_DIR = ROOT_DIR / "backend"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def count_files(path: Path) -> int | str:
    if not path.is_dir():
        return "-"
    return sum(1 for item in path.rglob("*") if item.is_file())


def format_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)}{unit}"
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{int(num_bytes)}B"


def get_path_size(path: Path) -> str:
    if not path.exists():
        return "-"
    if path.is_file() and not path.is_symlink():
        return format_size(path.stat().st_size)

    total = 0
    for item in path.rglob("*") if path.is_dir() else []:
        if item.is_file() and not item.is_symlink():
            total += item.stat().st_size
    return format_size(total)


def report_line(path: Path) -> str:
    if not path.exists() and not path.is_symlink():
        return f"{str(path):<55} | exists=no  | type=-    | files=-        | size=-"

    if path.is_symlink():
        kind = "link"
    elif path.is_dir():
        kind = "dir"
    else:
        kind = "file"

    return (
        f"{str(path):<55} | exists=yes | type={kind:<4} | "
        f"files={str(count_files(path)):<8} | size={get_path_size(path)}"
    )


def log_message(lines: Iterable[str], log_prefix: str) -> Path:
    ensure_directory(LOG_DIR)
    log_path = LOG_DIR / f"{log_prefix}_{TIMESTAMP}.log"
    content = "\n".join(lines) + "\n"
    log_path.write_text(content, encoding="utf-8")
    print(content, end="")
    print(f"log written to: {log_path}")
    return log_path


def copy_missing_tree(src: Path, dst: Path) -> list[str]:
    messages: list[str] = []
    if not src.is_dir():
        messages.append(f"skip missing source: {src}")
        return messages

    ensure_directory(dst)
    copied = 0
    skipped = 0
    for item in sorted(src.rglob("*")):
        relative = item.relative_to(src)
        target = dst / relative
        if item.is_dir():
            ensure_directory(target)
            continue
        if target.exists():
            skipped += 1
            continue
        ensure_directory(target.parent)
        target.write_bytes(item.read_bytes())
        copied += 1
    messages.append(f"sync missing files: {src} -> {dst} | copied={copied} skipped={skipped}")
    return messages


def latest_backup(prefix: str) -> Path | None:
    candidates = sorted(LEGACY_RUNTIME_DIR.glob(f"{prefix}_*"))
    return candidates[-1] if candidates else None


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.is_dir():
        for child in sorted(path.iterdir(), reverse=True):
            remove_path(child)
        path.rmdir()


def create_symlink(target: Path, link_path: Path) -> None:
    if link_path.exists() or link_path.is_symlink():
        raise FileExistsError(f"path already exists: {link_path}")
    os.symlink(target, link_path)
