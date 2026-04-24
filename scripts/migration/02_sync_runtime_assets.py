from __future__ import annotations

from datetime import datetime

from _common import BACKEND_DIR, LEGACY_KNOWLEDGE_DIR, ROOT_DIR, copy_missing_tree, get_path_size, log_message


if __name__ == "__main__":
    lines = [
        f"[migration sync] started at {datetime.now().astimezone().isoformat()}",
        f"root: {ROOT_DIR}",
        "",
    ]

    lines.extend(copy_missing_tree(ROOT_DIR / "uploads", BACKEND_DIR / "uploads"))
    lines.extend(copy_missing_tree(ROOT_DIR / "exports", BACKEND_DIR / "exports"))
    lines.extend(copy_missing_tree(ROOT_DIR / "snapshots", BACKEND_DIR / "snapshots"))
    lines.extend(copy_missing_tree(ROOT_DIR / "rules", LEGACY_KNOWLEDGE_DIR / "rules"))
    lines.extend(copy_missing_tree(ROOT_DIR / "templates", LEGACY_KNOWLEDGE_DIR / "templates"))

    lines.extend(
        [
            "",
            "post-sync summary:",
            f"{BACKEND_DIR / 'uploads'} size={get_path_size(BACKEND_DIR / 'uploads')}",
            f"{BACKEND_DIR / 'exports'} size={get_path_size(BACKEND_DIR / 'exports')}",
            f"{BACKEND_DIR / 'snapshots'} size={get_path_size(BACKEND_DIR / 'snapshots')}",
            "",
            f"[migration sync] finished at {datetime.now().astimezone().isoformat()}",
        ]
    )

    log_message(lines, "migration_sync")
