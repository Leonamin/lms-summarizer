"""SQLite records. Only the owning supervisor process opens this repository."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import threading

SCHEMA = """
CREATE TABLE settings_revisions (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE jobs (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, status TEXT NOT NULL,
 current_attempt_id TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL);
CREATE TABLE attempts (id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id),
 number INTEGER NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, UNIQUE(job_id,number));
CREATE TABLE artifacts (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, state TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE stage_runs (id TEXT PRIMARY KEY, attempt_id TEXT NOT NULL REFERENCES attempts(id),
 stage INTEGER NOT NULL, status TEXT NOT NULL, input_id TEXT REFERENCES artifacts(id),
 output_id TEXT REFERENCES artifacts(id), payload TEXT NOT NULL, UNIQUE(attempt_id,stage));
CREATE INDEX stage_queue ON stage_runs(stage,status);
CREATE INDEX owner_jobs ON jobs(owner_id,status);
CREATE TABLE events (seq INTEGER PRIMARY KEY AUTOINCREMENT, owner_id TEXT NOT NULL,
 job_id TEXT, type TEXT NOT NULL, payload TEXT NOT NULL, timestamp TEXT NOT NULL);
CREATE TABLE idempotency (owner_id TEXT NOT NULL, operation TEXT NOT NULL, key TEXT NOT NULL,
 fingerprint TEXT NOT NULL, result TEXT NOT NULL, PRIMARY KEY(owner_id,operation,key));
"""

def utcnow():
    return datetime.now(timezone.utc).isoformat()

class JobRepository:
    def __init__(self, path: Path):
        self.lock = threading.RLock()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, timeout=5, isolation_level=None, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA busy_timeout=5000")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version > 1:
            self.connection.close()
            raise RuntimeError("Unsupported database schema")
        if version == 0:
            self.connection.executescript("BEGIN IMMEDIATE;" + SCHEMA + "PRAGMA user_version=1; COMMIT;")

    @contextmanager
    def transaction(self):
        with self.lock:
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                yield self
                self.connection.execute("COMMIT")
            except BaseException:
                self.connection.execute("ROLLBACK")
                raise

    def execute(self, sql, args=()):
        return self.connection.execute(sql, args)

    def insert(self, table, record, **columns):
        allowed = {"jobs", "attempts", "artifacts", "stage_runs", "settings_revisions"}
        if table not in allowed:
            raise ValueError("Unknown record table")
        values = {"id": record["id"], **columns, "payload": json.dumps(record, ensure_ascii=False)}
        names = ','.join(values)
        placeholders = ','.join('?' for _ in values)
        self.execute(f"INSERT INTO {table} ({names}) VALUES ({placeholders})", tuple(values.values()))

    def update(self, table, record, **columns):
        if table not in {"jobs", "attempts", "artifacts", "stage_runs"}:
            raise ValueError("Unknown record table")
        values = {**columns, "payload": json.dumps(record, ensure_ascii=False)}
        self.execute(f"UPDATE {table} SET " + ','.join(f'{k}=?' for k in values) + " WHERE id=?", (*values.values(), record['id']))

    def get(self, table, record_id):
        if table not in {"jobs", "attempts", "artifacts", "stage_runs", "settings_revisions"}:
            raise ValueError("Unknown record table")
        row = self.execute(f"SELECT payload FROM {table} WHERE id=?", (record_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def records(self, sql, args=()):
        return [json.loads(row['payload']) for row in self.execute(sql, args).fetchall()]

    def event(self, owner, job, kind, payload):
        self.execute("INSERT INTO events(owner_id,job_id,type,payload,timestamp) VALUES(?,?,?,?,?)",
                     (owner, job, kind, json.dumps(payload), utcnow()))

    def close(self):
        self.connection.close()
