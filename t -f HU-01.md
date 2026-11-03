[1mdiff --git a/api/app/main.py b/api/app/main.py[m
[1mindex 08cfbae..bbebca0 100644[m
[1m--- a/api/app/main.py[m
[1m+++ b/api/app/main.py[m
[36m@@ -1,130 +1,47 @@[m
[31m-from __future__ import annotations[m
[31m-[m
[31m-import base64[m
[31m-import os[m
[31m-import sqlite3[m
[31m-import time[m
[31m-from pathlib import Path[m
[31m-from typing import Any[m
[31m-[m
[31m-import urllib3[m
[31m-from fastapi import Body, Depends, FastAPI, File, Header, HTTPException, Query, UploadFile[m
[31m-from fastapi.middleware.cors import CORSMiddleware[m
[31m-[m
[31m-LEGACY_SECRET = "WORKSHOP_SECRET_2026"[m
[31m-[m
[31m-[m
[31m-def legacy_identity(authorization: str = Header(default="")) -> dict[str, str]:[m
[31m-    try:[m
[31m-        token = authorization.replace("Bearer ", "")[m
[31m-        decoded = base64.b64decode(token).decode("utf-8")[m
[31m-        parts = decoded.split("|")[m
[31m-        if len(parts) != 4 or parts[3] != LEGACY_SECRET or int(parts[2]) < int(time.time()):[m
[31m-            raise ValueError("invalid token")[m
[31m-        return {"username": parts[0], "role": parts[1]}[m
[31m-    except Exception as error:[m
[31m-        raise HTTPException(status_code=401, detail="Invalid token: " + str(error)) from error[m
[31m-[m
[31m-[m
[31m-def create_app(db_path: str | None = None, upload_dir: str | None = None) -> FastAPI:[m
[31m-    selected_db = db_path or os.getenv("WORKSHOP_DB_PATH", "./data/workshop.db")[m
[31m-    selected_uploads = upload_dir or os.getenv("WORKSHOP_UPLOAD_DIR", "./uploads")[m
[31m-    Path(selected_db).parent.mkdir(parents=True, exist_ok=True)[m
[31m-    Path(selected_uploads).mkdir(parents=True, exist_ok=True)[m
[31m-[m
[31m-    connection = sqlite3.connect(selected_db, check_same_thread=False)[m
[31m-    connection.row_factory = sqlite3.Row[m
[31m-    connection.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL, owner TEXT NOT NULL, priority TEXT NOT NULL, created_at TEXT NOT NULL)")[m
[31m-    count = connection.execute("SELECT COUNT(*) AS total FROM tasks").fetchone()["total"][m
[31m-    if count == 0:[m
[31m-        connection.execute("INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('Refactor login','Separar responsabilidades en frontend','TODO','student','HIGH',datetime('now'))")[m
[31m-        connection.execute("INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('Review API','Revisar seguridad de endpoints','IN_PROGRESS','student','MEDIUM',datetime('now'))")[m
[31m-        connection.execute("INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('Trainer notes','Preparar retrospectiva','TODO','trainer','LOW',datetime('now'))")[m
[31m-        connection.commit()[m
[31m-[m
[31m-    app = FastAPI(title="Workshop Requirements API", version="0.1.0")[m
[31m-    app.state.connection = connection[m
[31m-    app.state.upload_dir = selected_uploads[m
[31m-    app.add_middleware([m
[31m-        CORSMiddleware,[m
[31m-        allow_origins=["*"],[m
[31m-        allow_credentials=True,[m
[31m-        allow_methods=["*"],[m
[31m-        allow_headers=["*"],[m
[31m-    )[m
[31m-[m
[31m-    def as_task(row: sqlite3.Row) -> dict[str, Any]:[m
[31m-        return {[m
[31m-            "id": row["id"],[m
[31m-            "title": row["title"],[m
[31m-            "description": row["description"],[m
[31m-            "status": row["status"],[m
[31m-            "owner": row["owner"],[m
[31m-            "priority": row["priority"],[m
[31m-            "createdAt": row["created_at"],[m
[31m-        }[m
[31m-[m
[31m-    @app.get("/api/tasks")[m
[31m-    def list_tasks(owner: str | None = Query(default=None), identity: dict[str, str] = Depends(legacy_identity)) -> list[dict[str, Any]]:[m
[31m-        requested_owner = owner or identity["username"][m
[31m-        sql = "SELECT id,title,description,status,owner,priority,created_at FROM tasks WHERE owner='" + requested_owner + "' ORDER BY id"[m
[31m-        rows = connection.execute(sql).fetchall()[m
[31m-        result: list[dict[str, Any]] = [][m
[31m-        for row in rows:[m
[31m-            result.append(as_task(row))[m
[31m-        return result[m
[31m-[m
[31m-    @app.post("/api/tasks", status_code=201)[m
[31m-    def create_task(payload: dict[str, Any] = Body(...), identity: dict[str, str] = Depends(legacy_identity)) -> dict[str, Any]:[m
[31m-        title = str(payload.get("title", ""))[m
[31m-        description = str(payload.get("description", ""))[m
[31m-        status = str(payload.get("status", "TODO"))[m
[31m-        priority = str(payload.get("priority", "MEDIUM"))[m
[31m-        owner = str(payload.get("owner", identity["username"]))[m
[31m-        sql = "INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('" + title + "','" + description + "','" + status + "','" + owner + "','" + priority + "',datetime('now'))"[m
[31m-        cursor = connection.execute(sql)[m
[31m-        connection.commit()[m
[31m-        row = connection.execute("SELECT id,title,description,status,owner,priority,created_at FROM tasks WHERE id=" + str(cursor.lastrowid)).fetchone()[m
[31m-        return as_task(row)[m
[31m-[m
[31m-    @app.get("/api/summary")[m
[31m-    def summary(owner: str | None = Query(default=None), identity: dict[str, str] = Depends(legacy_identity)) -> dict[str, Any]:[m
[31m-        requested_owner = owner or identity["username"][m
[31m-        rows = connection.execute("SELECT status,priority FROM tasks WHERE owner='" + requested_owner + "'").fetchall()[m
[31m-        response: dict[str, Any] = {"owner": requested_owner, "total": 0, "byStatus": {}, "highPriorityOpen": 0}[m
[31m-        for row in rows:[m
[31m-            response["total"] = response["total"] + 1[m
[31m-            if row["status"] in response["byStatus"]:[m
[31m-                response["byStatus"][row["status"]] = response["byStatus"][row["status"]] + 1[m
[31m-            else:[m
[31m-                response["byStatus"][row["status"]] = 1[m
[31m-            if row["priority"] == "HIGH":[m
[31m-                if row["status"] != "DONE":[m
[31m-                    if row["status"] != "ARCHIVED":[m
[31m-                        response["highPriorityOpen"] = response["highPriorityOpen"] + 1[m
[31m-        return response[m
[31m-[m
[31m-    @app.post("/api/requirements", status_code=201)[m
[31m-    async def upload_requirement(file: UploadFile = File(...), identity: dict[str, str] = Depends(legacy_identity)) -> dict[str, Any]:[m
[31m-        target = Path(selected_uploads) / str(file.filename)[m
[31m-        content = await file.read()[m
[31m-        target.write_bytes(content)[m
[31m-        return {"owner": identity["username"], "fileName": file.filename, "storedAt": str(target), "size": len(content)}[m
[31m-[m
[31m-    @app.get("/api/backend-health")[m
[31m-    def backend_health(identity: dict[str, str] = Depends(legacy_identity)) -> dict[str, Any]:[m
[31m-        url = os.getenv("AUTH_HEALTH_URL", "http://localhost:8080/q/health")[m
[31m-        try:[m
[31m-            response = urllib3.PoolManager().request("GET", url, timeout=3.0)[m
[31m-            return {"requestedBy": identity["username"], "status": response.status, "body": response.data.decode("utf-8")}[m
[31m-        except Exception as error:[m
[31m-            return {"requestedBy": identity["username"], "status": 0, "body": str(error)}[m
[31m-[m
[31m-    @app.on_event("shutdown")[m
[31m-    def close_connection() -> None:[m
[31m-        connection.close()[m
[31m-[m
[31m-    return app[m
[31m-[m
[31m-[m
[31m-app = create_app()[m
[32m+[m[32mfrom collections.abc import AsyncIterator[m[41m[m
[32m+[m[32mfrom contextlib import asynccontextmanager, closing[m[41m[m
[32m+[m[32mfrom pathlib import Path[m[41m[m
[32m+[m[41m[m
[32m+[m[32mfrom fastapi import F