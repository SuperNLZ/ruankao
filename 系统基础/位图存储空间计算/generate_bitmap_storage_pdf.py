from pathlib import Path
import re

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, Preformatted, SimpleDocTemplate, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


BASE_DIR = Path(__file__).resolve().parent
MD_PATH = BASE_DIR / "位图存储空间计算-快速记忆.md"
PDF_PATH = BASE_DIR / "位图存储空间计算-快速记忆.pdf"

FONT_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
]


def pick_font_path():
    for font_path in FONT_CANDIDATES:
        if font_path.exists():
            return font_path
    return None


def register_font():
    font_path = pick_font_path()
    if font_path:
        pdfmetrics.registerFont(TTFont("CN", str(font_path)))
        return "CN"
    return "Helvetica"


def make_styles(font_name):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CnTitle", parent=styles["Title"], fontName=font_name, fontSize=21, leading=30, alignment=TA_CENTER, spaceAfter=14))
    styles.add(ParagraphStyle(name="CnH2", parent=styles["Heading2"], fontName=font_name, fontSize=15, leading=22, spaceBefore=10, spaceAfter=7, textColor=colors.HexColor("#1f2937")))
    styles.add(ParagraphStyle(name="CnBody", parent=styles["BodyText"], fontName=font_name, fontSize=10.5, leading=17, spaceAfter=7))
    styles.add(ParagraphStyle(name="CnCode", parent=styles["Code"], fontName=font_name, fontSize=9.5, leading=14, backColor=colors.HexColor("#f3f4f6"), borderColor=colors.HexColor("#e5e7eb"), borderWidth=0.6, borderPadding=6, spaceBefore=4, spaceAfter=8))
    return styles


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "")


def markdown_to_flowables(md_text, styles, doc_width):
    flowables = []
    paragraph_lines = []
    code_lines = []
    in_code = False

    def flush_para():
        nonlocal paragraph_lines
        if paragraph_lines:
            flowables.append(Paragraph(escape(" ".join(x.strip() for x in paragraph_lines)), styles["CnBody"]))
            paragraph_lines = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            flowables.append(Preformatted("\n".join(code_lines), styles["CnCode"]))
            code_lines = []

    for raw_line in md_text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_para()
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue

        image_match = re.match(r"!\[(.*?)\]\((.*?)\)", line)
        if image_match:
            flush_para()
            image_path = (BASE_DIR / image_match.group(2)).resolve()
            if image_path.exists():
                pil_img = PILImage.open(image_path)
                width, height = pil_img.size
                render_width = doc_width
                render_height = height * render_width / width
                flowables.append(Image(str(image_path), width=render_width, height=render_height))
                flowables.append(Spacer(1, 8))
            else:
                flowables.append(Paragraph(f"图片缺失：{escape(str(image_path))}", styles["CnBody"]))
            continue

        if line.startswith("# "):
            flush_para()
            flowables.append(Paragraph(escape(line[2:].strip()), styles["CnTitle"]))
        elif line.startswith("## "):
            flush_para()
            flowables.append(Paragraph(escape(line[3:].strip()), styles["CnH2"]))
        elif not line.strip():
            flush_para()
        else:
            paragraph_lines.append(line)

    flush_para()
    flush_code()
    return flowables


def build_pdf():
    font_name = register_font()
    styles = make_styles(font_name)
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="位图存储空间计算-快速记忆",
        author="Codex",
    )
    md_text = MD_PATH.read_text(encoding="utf-8")
    doc.build(markdown_to_flowables(md_text, styles, doc.width))


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
