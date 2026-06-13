from dataclasses import dataclass


@dataclass
class Favorit:
    id:            int
    tmdb_id:       int
    judul:         str
    genre:         str           = ""
    rating:        float         = 0.0
    catatan:       str           = ""
    poster_path:   str           = ""
    backdrop_path: str           = ""
    overview:      str           = ""
    release_year:  str           = ""
    tanggal_tambah: str          = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Favorit":
        return cls(
            id             = d.get("id", 0),
            tmdb_id        = d.get("tmdb_id", 0),
            judul          = d.get("judul", ""),
            genre          = d.get("genre", ""),
            rating         = float(d.get("rating", 0)),
            catatan        = d.get("catatan", ""),
            poster_path    = d.get("poster_path", ""),
            backdrop_path  = d.get("backdrop_path", ""),
            overview       = d.get("overview", ""),
            release_year   = d.get("release_year", ""),
            tanggal_tambah = d.get("tanggal_tambah", ""),
        )

    def to_dict(self) -> dict:
        return {
            "id":             self.id,
            "tmdb_id":        self.tmdb_id,
            "judul":          self.judul,
            "genre":          self.genre,
            "rating":         self.rating,
            "catatan":        self.catatan,
            "poster_path":    self.poster_path,
            "backdrop_path":  self.backdrop_path,
            "overview":       self.overview,
            "release_year":   self.release_year,
            "tanggal_tambah": self.tanggal_tambah,
        }
