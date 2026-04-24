from __future__ import annotations

from datetime import datetime

from _common import BACKEND_DIR, LEGACY_RUNTIME_DIR, ROOT_DIR, create_symlink, ensure_directory, log_message


def cutover_dir(name: str, timestamp: str) -> list[str]:
    root_target = ROOT_DIR / name
    backend_target = BACKEND_DIR / name
    legacy_target = LEGACY_RUNTIME_DIR / f"{name}_{timestamp}"
    ensure_directory(backend_target)
    ensure_directory(LEGACY_RUNTIME_DIR)

    messages: list[str] = []
    if root_target.is_symlink():
        messages.append(f"skip {name}: root path is already a symlink")
        return messages

    if root_target.is_dir():
        messages.append(f"move root directory to legacy backup: {root_target} -> {legacy_target}")
        root_target.rename(legacy_target)
    elif root_target.exists():
        raise RuntimeError(f"abort {name}: root path exists but is not a directory")
    else:
        messages.append(f"root path missing for {name}, only creating compatibility symlink")

    create_symlink(backend_target, root_target)
    messages.append(f"create compatibility symlink: {root_target} -> {backend_target}")
    return messages


if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    lines = [
        f"[migration cutover] started at {datetime.now().astimezone().isoformat()}",
        f"root: {ROOT_DIR}",
        "",
    ]

    for name in ("uploads", "exports", "snapshots"):
        lines.extend(cutover_dir(name, timestamp))

    lines.extend(
        [
            "",
            "compatibility links:",
            str((ROOT_DIR / "uploads").resolve()) if (ROOT_DIR / "uploads").exists() else str(ROOT_DIR / "uploads"),
            str((ROOT_DIR / "exports").resolve()) if (ROOT_DIR / "exports").exists() else str(ROOT_DIR / "exports"),
            str((ROOT_DIR / "snapshots").resolve()) if (ROOT_DIR / "snapshots").exists() else str(ROOT_DIR / "snapshots"),
            "",
            f"[migration cutover] finished at {datetime.now().astimezone().isoformat()}",
        ]
    )

    log_message(lines, "migration_cutover")
