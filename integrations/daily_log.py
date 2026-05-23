"""
Daily Log — database layer for daily work log entries.
"""

from db.database import get_connection
from services.logger import info


def init_daily_log_tables() -> None:
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            project_name TEXT NOT NULL,
            list_name TEXT NOT NULL,
            task_name TEXT NOT NULL,
            task_id TEXT DEFAULT '',
            progress INTEGER NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_dl_date ON daily_logs(date);
    """)
    conn.commit()
    conn.close()
    info("Daily log tables ready")


def add_log_entry(
    date: str,
    project_name: str,
    list_name: str,
    task_name: str,
    task_id: str = "",
    progress: int = 0,
    notes: str = "",
) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO daily_logs (date, project_name, list_name, task_name, task_id, progress, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (date, project_name, list_name, task_name, task_id, progress, notes),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_logs_by_date(date: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM daily_logs WHERE date = ? ORDER BY id", (date,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_logs(limit: int = 20) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM daily_logs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_log_entry(entry_id: int) -> bool:
    conn = get_connection()
    cursor = conn.execute("DELETE FROM daily_logs WHERE id = ?", (entry_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def generate_report(date: str) -> str:
    """
    Generate a formatted daily report in the style:
    - (Project) List > Task: 100%
      Notes here
      More notes
    """
    logs = get_logs_by_date(date)

    if not logs:
        return f"No hay registros para {date}"

    lines: list[str] = []
    lines.append(f"📋 Reporte diario — {date}")
    lines.append("")

    # Group by project
    projects: dict[str, list[dict]] = {}
    for log in logs:
        proj = log["project_name"]
        if proj not in projects:
            projects[proj] = []
        projects[proj].append(log)

    for proj, entries in projects.items():
        for entry in entries:
            task_line = f"- ({proj}) {entry['list_name']} > {entry['task_name']}: {entry['progress']}%"
            lines.append(task_line)

            if entry["notes"]:
                for note in entry["notes"].split("\n"):
                    note = note.strip()
                    if note:
                        lines.append(f"  {note}")

            lines.append("")  # blank line between entries

    return "\n".join(lines).strip()
