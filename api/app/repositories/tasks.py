import sqlite3

TASK_COLUMNS = "id,title,description,status,owner,priority,created_at"


class TaskRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def list_by_owner(self, owner: str) -> list[sqlite3.Row]:
        sql = "SELECT " + TASK_COLUMNS + " FROM tasks WHERE owner = ? ORDER BY id"
        return self._connection.execute(sql, (owner,)).fetchall()

    def status_and_priority_by_owner(self, owner: str) -> list[sqlite3.Row]:
        return self._connection.execute("SELECT status,priority FROM tasks WHERE owner = ?", (owner,)).fetchall()

    def create(self, title: str, description: str, status: str, owner: str, priority: str) -> sqlite3.Row:
        cursor = self._connection.execute(
            "INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES (?,?,?,?,?,datetime('now'))",
            (title, description, status, owner, priority),
        )
        self._connection.commit()
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, task_id: int) -> sqlite3.Row:
        return self._connection.execute("SELECT " + TASK_COLUMNS + " FROM tasks WHERE id = ?", (task_id,)).fetchone()
