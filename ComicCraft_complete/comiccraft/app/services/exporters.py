from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from fpdf import FPDF
from PIL import Image
from app.config import Settings
from app.models import ComicLayout

class ComicPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "ComicCraft", align="C")
        self.ln(12)

def _pdf_safe(value: str) -> str:
    return value.encode("latin-1", "replace").decode("latin-1")

def save_pdf(layout: list[ComicLayout], settings: Settings) -> str:
    if not layout:
        raise ValueError("Cannot export an empty comic")
    pdf = ComicPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    for panel in layout:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.multi_cell(180, 10,  _pdf_safe(f"Panel {panel.panel_number}: {panel.title}"))
        image_file = _local_image(settings, panel.image_path)
        with Image.open(image_file) as img:
            w, h = img.size
        max_w, max_h = 180, 105
        ratio = min(max_w / w, max_h / h)
        pdf.image(str(image_file), x=(210 - w * ratio) / 2, y=40, w=w * ratio, h=h * ratio)
        pdf.set_xy(15, 40 + h * ratio + 8)
        pdf.set_font("Helvetica", "I", 10)
        pdf.multi_cell(180, 6, _pdf_safe(panel.scene_description))
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(180, 6, _pdf_safe(panel.caption))
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(180, 6, _pdf_safe(panel.narration))
        for line in panel.dialogue:
            pdf.set_font("Helvetica", "I", 10)
            pdf.multi_cell(180, 6, f'"{_pdf_safe(line)}"')
    filename = f"comic_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}.pdf"
    target = settings.exports_dir / filename
    pdf.output(str(target))
    return f"/static/exports/{filename}"

def _local_image(settings: Settings, image_path: str) -> Path:
    path = urlparse(image_path).path
    name = Path(path).name
    candidate = settings.panels_dir / name
    if not candidate.exists():
        raise FileNotFoundError(f"Panel image not found: {candidate}")
    return candidate
