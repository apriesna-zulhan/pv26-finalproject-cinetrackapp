import csv
from datetime import datetime
from typing import List


def export_csv(data: List[dict], filepath: str) -> bool:
    try:
        fieldnames = [
            "id", "judul", "genre", "rating",
            "release_year", "catatan", "tanggal_tambah"
        ]
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        print(f"[CSV Export Error] {e}")
        return False


def export_pdf(data: List[dict], filepath: str, title: str = "Daftar Film Favorit") -> bool:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                        Paragraph, Spacer)

        doc = SimpleDocTemplate(
            filepath, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "title", parent=styles["Title"], fontSize=16, spaceAfter=6
        )
        sub_style = ParagraphStyle(
            "sub", parent=styles["Normal"],
            fontSize=9, textColor=colors.grey, spaceAfter=12
        )

        story = []
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(
            f"Diekspor pada {datetime.now().strftime('%d %B %Y, %H:%M')} — "
            f"Total {len(data)} film",
            sub_style
        ))
        story.append(Spacer(1, 0.3*cm))

        headers = ["No", "Judul", "Genre", "Rating", "Tahun", "Catatan"]
        rows = [headers]
        for i, d in enumerate(data, 1):
            catatan = (d.get("catatan") or "")[:40]
            if len(d.get("catatan") or "") > 40:
                catatan += "..."
            rows.append([
                str(i),
                (d.get("judul") or "")[:40],
                d.get("genre") or "-",
                f"{float(d.get('rating', 0)):.1f}",
                d.get("release_year") or "-",
                catatan,
            ])

        col_widths = [1*cm, 6*cm, 3*cm, 2*cm, 2*cm, 4.5*cm]
        table = Table(rows, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E50914")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, 0), 9),
            ("FONTSIZE",   (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#F5F5F5"), colors.white]),
            ("TEXTCOLOR",  (0, 1), (-1, -1), colors.HexColor("#141414")),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ]))
        story.append(table)
        doc.build(story)
        return True

    except ImportError:
        return _export_html_fallback(data, filepath.replace(".pdf", ".html"), title)
    except Exception as e:
        print(f"[PDF Export Error] {e}")
        return False


def _export_html_fallback(data: List[dict], filepath: str, title: str) -> bool:
    try:
        rows_html = ""
        for i, d in enumerate(data, 1):
            catatan = (d.get("catatan") or "")[:60]
            rows_html += (
                f"<tr><td>{i}</td><td>{d.get('judul','')}</td>"
                f"<td>{d.get('genre','-')}</td>"
                f"<td>{float(d.get('rating',0)):.1f}</td>"
                f"<td>{d.get('release_year','-')}</td>"
                f"<td>{catatan}</td></tr>"
            )

        html = (
            "<!DOCTYPE html><html lang='id'><head><meta charset='UTF-8'>"
            f"<title>{title}</title>"
            "<style>"
            "body{background:#141414;color:#E5E5E5;font-family:Segoe UI,sans-serif;padding:32px}"
            "h1{color:#E50914}p{color:#808080;font-size:12px}"
            "table{border-collapse:collapse;width:100%;margin-top:16px}"
            "th{background:#E50914;color:white;padding:8px 12px;text-align:left;font-size:12px}"
            "td{padding:7px 12px;font-size:12px;border-bottom:1px solid #2A2A2A}"
            "tr:nth-child(even) td{background:#1F1F1F}"
            "</style></head><body>"
            f"<h1>{title}</h1>"
            f"<p>Diekspor pada {datetime.now().strftime('%d %B %Y, %H:%M')} &nbsp;·&nbsp; Total {len(data)} film</p>"
            "<table><thead><tr>"
            "<th>#</th><th>Judul</th><th>Genre</th><th>Rating</th><th>Tahun</th><th>Catatan</th>"
            f"</tr></thead><tbody>{rows_html}</tbody></table></body></html>"
        )
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return True
    except Exception as e:
        print(f"[HTML Export Error] {e}")
        return False
