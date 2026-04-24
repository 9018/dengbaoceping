from __future__ import annotations

from datetime import datetime

from _common import ROOT_DIR, ensure_directory, latest_backup, log_message


def restore_dir(name: str) -> list[str]:
    root_target = ROOT_DIR / name
    backup = latest_backup(name)
    messages: list[str] = []

    if root_target.is_symlink():
        messages.append(f"remove compatibility symlink: {root_target}")
        root_target.unlink()
    elif root_target.exists():
        raise RuntimeError(f"abort {name}: root path exists and is not a symlink")

    if backup is None:
        ensure_directory(root_target)
        messages.append(f"no legacy backup found for {name}, recreated empty directory: {root_target}")
        return messages

    backup.rename(root_target)
    messages.append(f"restore legacy backup: {backup} -> {root_target}")
    return messages


if __name__ == "__main__":
    lines = [
        f"[migration rollback] started at {datetime.now().astimezone().isoformat()}",
        f"root: {ROOT_DIR}",
        "",
    ]

    for name in ("uploads", "exports", "snapshots"):
        lines.extend(restore_dir(name))

    lines.extend(
        [
            "",
            "restored root directories:",
            str(ROOT_DIR / "uploads"),
            str(ROOT_DIR / "exports"),
            str(ROOT_DIR / "snapshots"),
            "",
            f"[migration rollback] finished at {datetime.now().astimezone().isoformat()}",
        ]
    )

    log_message(lines, "migration_rollback")
