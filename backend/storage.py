import json
import os
import sqlite3
import time
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
      CREATE TABLE IF NOT EXISTS rate_limits (
        key TEXT NOT NULL, bucket INTEGER NOT NULL, count INTEGER NOT NULL,
        expires_at REAL NOT NULL, PRIMARY KEY(key,bucket)
      );
    ''')
    columns = {r['name'] for r in con.execute('PRAGMA table_info(sessions)')}
    for name, declaration in [('owner_hash', 'TEXT'), ('expires_at', 'REAL')]:
        if name not in columns:
            con.execute(f'ALTER TABLE sessions ADD COLUMN {name} {declaration}')
    con.execute('CREATE INDEX IF NOT EXISTS sessions_owner ON sessions(owner_hash)')
    con.execute('CREATE INDEX IF NOT EXISTS sessions_expiry ON sessions(expires_at)')
    con.commit()
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


def session(con, session_id: str, owner_hash: str, hosted: bool = False):
    row = con.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone()
    if (not row or (row['owner_hash'] and row['owner_hash'] != owner_hash)
            or (hosted and not row['owner_hash']) or (row['expires_at'] and row['expires_at'] <= time.time())):
        from fastapi import HTTPException
        raise HTTPException(404, 'This draft was not found in this browser, or it expired. Start a new form.')
    return dict(row)


def public_session(row):
    return {k: json.loads(row[k]) if k in ('answers', 'checklist') else row[k]
            for k in ('id', 'form_id', 'source_hash', 'answers', 'checklist', 'step', 'revision', 'status', 'receipt', 'updated_at')}


def purge_expired(con):
    con.execute('DELETE FROM events WHERE session_id IN (SELECT id FROM sessions WHERE expires_at <= ?)', (time.time(),))
    con.execute('DELETE FROM sessions WHERE expires_at <= ?', (time.time(),))
