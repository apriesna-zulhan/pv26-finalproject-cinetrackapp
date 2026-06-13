import sqlite3
from typing import Optional

DB_PATH = "cinetrack.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS favorit (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id        INTEGER UNIQUE,
    judul          TEXT NOT NULL,
    genre          TEXT DEFAULT '',
    rating         REAL DEFAULT 0.0,
    catatan        TEXT DEFAULT '',
    poster_path    TEXT DEFAULT '',
    backdrop_path  TEXT DEFAULT '',
    overview       TEXT DEFAULT '',
    release_year   TEXT DEFAULT '',
    tanggal_tambah TEXT DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS riwayat (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id        INTEGER,
    jenis          TEXT NOT NULL DEFAULT 'pencarian',
    keterangan     TEXT DEFAULT '',
    waktu          TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (tmdb_id) REFERENCES favorit(tmdb_id) ON DELETE SET NULL
);
"""


class DatabaseManager:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        with self._conn() as c:
            for stmt in SCHEMA.strip().split(";"):
                s = stmt.strip()
                if s:
                    c.execute(s)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def tambah(self, tmdb_id: Optional[int], judul: str, genre: str = "",
                rating: float = 0.0, catatan: str = "",
                poster_path: str = "", backdrop_path: str = "",
                overview: str = "", release_year: str = "") -> int:
        with self._conn() as c:
            if tmdb_id is not None:
                sql = """INSERT OR REPLACE INTO favorit
                         (tmdb_id,judul,genre,rating,catatan,poster_path,backdrop_path,overview,release_year)
                         VALUES (?,?,?,?,?,?,?,?,?)"""
                cur = c.execute(sql, (tmdb_id, judul, genre, rating, catatan,
                                      poster_path, backdrop_path, overview, release_year))
            else:
                sql = """INSERT INTO favorit
                         (tmdb_id,judul,genre,rating,catatan,poster_path,backdrop_path,overview,release_year)
                         VALUES (NULL,?,?,?,?,?,?,?,?)"""
                cur = c.execute(sql, (judul, genre, rating, catatan,
                                      poster_path, backdrop_path, overview, release_year))
            fid = cur.lastrowid
            c.execute(
                "INSERT INTO riwayat (tmdb_id, jenis, keterangan) VALUES (?,?,?)",
                (tmdb_id, "tambah_favorit", f"Menambahkan \"{judul}\" ke favorit")
            )
            return fid

    def semua(self) -> list[dict]:
        with self._conn() as c:
            return [dict(r) for r in c.execute("SELECT * FROM favorit ORDER BY id DESC")]

    def by_id(self, fid: int) -> Optional[dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM favorit WHERE id=?", (fid,)).fetchone()
            return dict(r) if r else None

    def by_tmdb(self, tmdb_id: int) -> Optional[dict]:
        if tmdb_id is None:
            return None
        with self._conn() as c:
            r = c.execute("SELECT * FROM favorit WHERE tmdb_id=?", (tmdb_id,)).fetchone()
            return dict(r) if r else None

    def tmdb_ids(self) -> set[int]:
        with self._conn() as c:
            rows = c.execute("SELECT tmdb_id FROM favorit WHERE tmdb_id IS NOT NULL").fetchall()
            return {r[0] for r in rows}

    def count(self) -> int:
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) FROM favorit").fetchone()[0]

    def avg_rating(self) -> float:
        with self._conn() as c:
            v = c.execute("SELECT AVG(rating) FROM favorit WHERE rating>0").fetchone()[0]
            return round(v, 1) if v else 0.0

    def update(self, fid: int, judul: str, genre: str,
               rating: float, catatan: str,
               release_year: str = "", poster_path: str = None) -> bool:
        if poster_path is None:
            sql = "UPDATE favorit SET judul=?,genre=?,rating=?,catatan=?,release_year=? WHERE id=?"
            params = (judul, genre, rating, catatan, release_year, fid)
        else:
            sql = "UPDATE favorit SET judul=?,genre=?,rating=?,catatan=?,release_year=?,poster_path=? WHERE id=?"
            params = (judul, genre, rating, catatan, release_year, poster_path, fid)

        with self._conn() as c:
            ok = c.execute(sql, params).rowcount > 0
            if ok:
                row = c.execute("SELECT tmdb_id FROM favorit WHERE id=?", (fid,)).fetchone()
                tmdb_id = row[0] if row else None
                c.execute(
                    "INSERT INTO riwayat (tmdb_id, jenis, keterangan) VALUES (?,?,?)",
                    (tmdb_id, "edit_favorit", f"Mengedit \"{judul}\"")
                )
            return ok

    def hapus(self, fid: int) -> bool:
        with self._conn() as c:
            row = c.execute("SELECT judul, tmdb_id FROM favorit WHERE id=?", (fid,)).fetchone()
            ok  = c.execute("DELETE FROM favorit WHERE id=?", (fid,)).rowcount > 0
            if ok and row:
                c.execute(
                    "INSERT INTO riwayat (tmdb_id, jenis, keterangan) VALUES (?,?,?)",
                    (row[1], "hapus_favorit", f"Menghapus \"{row[0]}\" dari favorit")
                )
            return ok

    def hapus_by_tmdb(self, tmdb_id: int) -> bool:
        with self._conn() as c:
            return c.execute("DELETE FROM favorit WHERE tmdb_id=?", (tmdb_id,)).rowcount > 0

    def tambah_riwayat(self, jenis: str, keterangan: str, tmdb_id: int = None):
        with self._conn() as c:
            c.execute(
                "INSERT INTO riwayat (tmdb_id, jenis, keterangan) VALUES (?,?,?)",
                (tmdb_id, jenis, keterangan)
            )

    def semua_riwayat(self, limit: int = 50) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM riwayat ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def hapus_semua_riwayat(self):
        with self._conn() as c:
            c.execute("DELETE FROM riwayat")
