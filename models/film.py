from dataclasses import dataclass, field


@dataclass
class Film:
    tmdb_id:       int
    judul:         str
    overview:      str           = ""
    poster_path:   str           = ""
    backdrop_path: str           = ""
    rating:        float         = 0.0
    popularity:    float         = 0.0
    release_year:  str           = ""
    genre_ids:     list[int]     = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict) -> "Film":
        release = data.get("release_date", "") or ""
        year    = release[:4] if len(release) >= 4 else ""
        return cls(
            tmdb_id       = data.get("id", 0),
            judul         = data.get("title") or data.get("name", ""),
            overview      = data.get("overview", ""),
            poster_path   = data.get("poster_path", "") or "",
            backdrop_path = data.get("backdrop_path", "") or "",
            rating        = float(data.get("vote_average", 0)),
            popularity    = float(data.get("popularity", 0)),
            release_year  = year,
            genre_ids     = data.get("genre_ids", []),
        )

    def to_dict(self) -> dict:
        return {
            "tmdb_id":       self.tmdb_id,
            "judul":         self.judul,
            "overview":      self.overview,
            "poster_path":   self.poster_path,
            "backdrop_path": self.backdrop_path,
            "rating":        self.rating,
            "popularity":    self.popularity,
            "release_year":  self.release_year,
            "genre_ids":     self.genre_ids,
        }
