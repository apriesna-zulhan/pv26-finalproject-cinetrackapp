import os

BG_BASE    = "#141414"
BG_SURFACE = "#1F1F1F"
BG_CARD    = "#2A2A2A"
BG_HOVER   = "#333333"
BG_INPUT   = "#242424"

RED        = "#E50914"
RED_HOVER  = "#F40612"
RED_DIM    = "#B20710"

WHITE      = "#FFFFFF"
GRAY_100   = "#E5E5E5"
GRAY_200   = "#B3B3B3"
GRAY_300   = "#808080"
GRAY_400   = "#4A4A4A"
GRAY_500   = "#2A2A2A"

GOLD       = "#F5C518"
GREEN_ACT  = "#46D369"
BLUE_ACT   = "#0071EB"

BORDER     = "#2A2A2A"

GENRE_COLORS = {
    28:"#E50914", 18:"#6B46C1", 35:"#D97706", 27:"#DC2626",
    878:"#2563EB", 16:"#059669", 10749:"#DB2777", 53:"#7C3AED",
    99:"#374151", 12:"#B45309", 14:"#4F46E5", 80:"#991B1B",
    36:"#78350F", 10751:"#0369A1", 10402:"#065F46", 9648:"#1E3A5F",
}
GENRE_NAMES = {
    28:"Aksi", 18:"Drama", 35:"Komedi", 27:"Horor", 878:"Sci-Fi",
    16:"Animasi", 10749:"Romantis", 53:"Thriller", 99:"Dokumenter",
    12:"Petualangan", 14:"Fantasi", 80:"Kriminal", 36:"Sejarah",
    10751:"Keluarga", 10402:"Musik", 9648:"Misteri",
}

def load_qss() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    qss_path = os.path.join(base, "assets", "style.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"[theme] Warning: {qss_path} tidak ditemukan, styling tidak diterapkan.")
        return ""
QSS = load_qss()
