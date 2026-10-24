import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def db():
    root = Path(os.environ.get('ACCESSPATH_DATA', 'data'))
    root.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(root / 'accesspath.sqlite3', timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA secure_delete=ON')
    con.executescript('''
      CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY, form_id TEXT NOT NULL, source_hash TEXT NOT NULL,
        answers TEXT NOT NULL DEFAULT '{}', checklist TEXT NOT NULL DEFAULT '[]',
        step INTEGER NOT NULL DEFAULT 0, revision INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'draft', token TEXT, token_at REAL,
        receipt TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, event TEXT NOT NULL,
        created_at TEXT NOT NULL, detail TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS explanations (cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL);
    ''')
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def event(con, session_id: str, name: str, detail: str):
    con.execute('INSERT INTO events(session_id,event,created_at,detail) VALUES(?,?,?,?)',
                (session_id, name, now(), detail))


def session(con, session_id: str):
    row = con.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, 'This local draft was not found.')
    return dict(row)


def public_session(row):
    return {k: json.loads(row[k]) if k in ('answers', 'checklist') else row[k]
            for k in ('id', 'form_id', 'source_hash', 'answers', 'checklist', 'step', 'revision', 'status', 'receipt', 'updated_at')}
