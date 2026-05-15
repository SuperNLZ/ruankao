from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS = [
    (
        BASE_DIR / "ISOIEC25010软件质量模型-概念讲解.md",
        BASE_DIR / "ISOIEC25010软件质量模型-概念讲解.pdf",
        "ISOIEC25010软件质量模型-概念讲解",
    ),
    (
        BASE_DIR / "ISOIEC25010软件质量模型-快速记忆.md",
        BASE_DIR / "ISOIEC25010软件质量模型-快速记忆.pdf",
        "ISOIEC25010软件质量模型-快速记忆",
    ),
]

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
    styles.add(ParagraphStyle(name="CnH3", parent=styles["Heading3"], fontName=font_name, fontSize=12.5, leading=18, spaceBefore=8, spaceAfter=5, textColor=colors.HexColor("#374151")))
    styles.add(ParagraphStyle(name="CnBody", parent=styles["BodyText"], fontName=font_name, fontSize=10.5, leading=17, spaceAfter=7))
    styles.add(ParagraphStyle(name="CnBullet", parent=styles["BodyText"], fontName=font_name, fontSize=10.5, leading=17, leftIndent=12, firstLineIndent=-8, spaceAfter=4))
    styles.add(ParagraphStyle(name="CnCode", parent=styles["Code"], fontName=font_name, fontSize=9.5, leading=14, backColor=colors.HexColor("#f3f4f6"), borderColor=colors.HexColor("#e5e7eb"), borderWidth=0.6, borderPadding=6, spaceBefore=4, spaceAfter=8))
    return styles


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "")


def markdown_to_flowables(md_text, styles):
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

        if line.startswith("# "):
            flush_para()
            flowables.append(Paragraph(escape(line[2:].strip()), styles["CnTitle"]))
        elif line.startswith("## "):
            flush_para()
            flowables.append(Paragraph(escape(line[3:].strip()), styles["CnH2"]))
        elif line.startswith("### "):
            flush_para()
            flowables.append(Paragraph(escape(line[4:].strip()), styles["CnH3"]))
        elif line.startswith("|"):
            flush_para()
            flowables.append(Paragraph(escape(line), styles["CnBody"]))
        elif line.startswith("- "):
            flush_para()
            flowables.append(Paragraph("• " + escape(line[2:].strip()), styles["CnBullet"]))
        elif re.match(r"^\d+\.\s+", line):
            flush_para()
            flowables.append(Paragraph(escape(line), styles["CnBullet"]))
        elif not line.strip():
            flush_para()
        else:
            paragraph_lines.append(line)

    flush_para()
    flush_code()
    return flowables


def build_pdf(md_path, pdf_path, title):
    font_name = register_font()
    styles = make_styles(font_name)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=title,
        author="Codex",
    )
    md_text = md_path.read_text(encoding="utf-8")
    doc.build(markdown_to_flowables(md_text, styles))


if __name__ == "__main__":
    for md_path, pdf_path, title in DOCUMENTS:
        build_pdf(md_path, pdf_path, title)
        print(pdf_path)
