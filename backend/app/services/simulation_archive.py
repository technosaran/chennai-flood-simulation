"""Local immutable simulation snapshots, compressed and integrity checked."""
import gzip
import hashlib
import json
import os
import sqlite3
import uuid
import zlib
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


class ArchiveCorrupt(ValueError):
    pass


class SimulationArchive:
    def __init__(self, path=None):
        self.path = Path(path or os.environ.get('SIM_ARCHIVE_DB') or Path(__file__).parents[2] / 'storage/simulations.sqlite3')

    @contextmanager
    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA journal_mode = WAL;')
        connection.execute('PRAGMA synchronous = NORMAL;')
        try:
            with connection:
                connection.execute('''CREATE TABLE IF NOT EXISTS snapshots (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, saved_at TEXT NOT NULL,
                    simulation_id TEXT NOT NULL, computed_at TEXT NOT NULL,
                    summary TEXT NOT NULL, sha256 TEXT NOT NULL, payload BLOB NOT NULL)''')
                yield connection
        finally:
            connection.close()

    def save(self, name, snapshot):
        raw = json.dumps(snapshot, separators=(',', ':'), allow_nan=False).encode('utf-8')
        result = snapshot['result']
        identity = 'saved_' + uuid.uuid4().hex
        saved = datetime.now(timezone.utc).isoformat()
        summary = json.dumps(dict(timeline_steps=len(result['timeline']),
                                  peak_affected=max(s['metrics']['total_affected_population'] for s in result['timeline']),
                                  fleet_included=any(s.get('rescue_fleet_plan') is not None for s in result['timeline']),
                                  imported=bool(snapshot.get('imported_from'))))
        with self.connect() as connection:
            connection.execute('INSERT INTO snapshots VALUES (?,?,?,?,?,?,?,?)',
                               (identity, name, saved, result['simulation_id'], result['computed_at'],
                                summary, hashlib.sha256(raw).hexdigest(), gzip.compress(raw)))
        return dict(id=identity, name=name, saved_at=saved)

    def list(self, offset=0, limit=20):
        with self.connect() as connection:
            rows = connection.execute('SELECT id,name,saved_at,simulation_id,computed_at,summary,length(payload) AS stored_bytes FROM snapshots ORDER BY saved_at DESC,id DESC LIMIT ? OFFSET ?', (limit, offset)).fetchall()
            total = connection.execute('SELECT count(*) FROM snapshots').fetchone()[0]
        return dict(total=total, items=[{**{k: row[k] for k in row.keys() if k != 'summary'}, **json.loads(row['summary'])} for row in rows])

    def get(self, identity):
        with self.connect() as connection:
            row = connection.execute('SELECT * FROM snapshots WHERE id=?', (identity,)).fetchone()
        if row is None:
            return None
        try:
            raw = gzip.decompress(row['payload'])
            if hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ArchiveCorrupt('Saved snapshot checksum mismatch')
            snapshot = json.loads(raw)
            if snapshot['schema_version'] != 1 or snapshot['result']['simulation_id'] != row['simulation_id'] or not snapshot['result']['timeline']:
                raise ArchiveCorrupt('Unsupported or incomplete saved snapshot')
        except (OSError, ValueError, KeyError, TypeError, EOFError, zlib.error) as exc:
            raise ArchiveCorrupt('This saved snapshot is damaged or unsupported. The active scenario was not changed.') from exc
        return dict(id=row['id'], name=row['name'], saved_at=row['saved_at'], read_only=True, **snapshot)
