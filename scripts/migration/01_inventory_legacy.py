from __future__ import annotations

from datetime import datetime
from pathlib import Path

from _common import BACKEND_DIR, LEGACY_KNOWLEDGE_DIR, LEGACY_RUNTIME_DIR, ROOT_DIR, log_message, report_line


if __name__ == "__main__":
    lines = [
        f"[migration inventory] started at {datetime.now().astimezone().isoformat()}",
        f"root: {ROOT_DIR}",
        "",
        "== legacy root directories ==",
        report_line(ROOT_DIR / "uploads"),
        report_line(ROOT_DIR / "exports"),
        report_line(ROOT_DIR / "snapshots"),
        report_line(ROOT_DIR / "rules"),
        report_line(ROOT_DIR / "templates"),
        report_line(ROOT_DIR / "docker"),
        "",
        "== backend mainline directories ==",
        report_line(BACKEND_DIR / "uploads"),
        report_line(BACKEND_DIR / "exports"),
        report_line(BACKEND_DIR / "snapshots"),
        report_line(BACKEND_DIR / "app" / "rules"),
        "",
        "== legacy target directories ==",
        report_line(LEGACY_RUNTIME_DIR / "uploads"),
        report_line(LEGACY_RUNTIME_DIR / "exports"),
        report_line(LEGACY_RUNTIME_DIR / "snapshots"),
        report_line(LEGACY_KNOWLEDGE_DIR / "rules"),
        report_line(LEGACY_KNOWLEDGE_DIR / "templates"),
        "",
        f"[migration inventory] finished at {datetime.now().astimezone().isoformat()}",
    ]
    log_message(lines, "migration_inventory")
