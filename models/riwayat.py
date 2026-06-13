from dataclasses import dataclass
from typing import Optional


@dataclass
class Riwayat:
    id:          int
    tmdb_id:     Optional[int]
    jenis:       str
    keterangan:  str  = ""
    waktu:       str  = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Riwayat":
        return cls(
            id         = d.get("id", 0),
            tmdb_id    = d.get("tmdb_id"),
            jenis      = d.get("jenis", ""),
            keterangan = d.get("keterangan", ""),
            waktu      = d.get("waktu", ""),
        )

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "tmdb_id":    self.tmdb_id,
            "jenis":      self.jenis,
            "keterangan": self.keterangan,
            "waktu":      self.waktu,
        }
