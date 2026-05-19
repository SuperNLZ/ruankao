from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image as PdfImage
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


BASE_DIR = Path(__file__).resolve().parent
MD_PATH = BASE_DIR / "阿姆达尔定律加速比计算解题过程.md"
PDF_PATH = BASE_DIR / "阿姆达尔定律加速比计算解题过程.pdf"
IMG_PATH = BASE_DIR / "images" / "阿姆达尔定律加速比计算-题目截图.png"

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


def pil_font(size):
    font_path = pick_font_path()
    if font_path:
        return ImageFont.truetype(str(font_path), size)
    return ImageFont.load_default()


def register_font():
    font_path = pick_font_path()
    if font_path:
        pdfmetrics.registerFont(TTFont("CN", str(font_path)))
        return "CN"
    return "Helvetica"


def draw_question_image():
    IMG_PATH.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1100, 520), "#d8eee1")
    draw = ImageDraw.Draw(img)
    title_font = pil_font(28)
    body_font = pil_font(24)
    small_font = pil_font(22)
    red = "#cc3333"
    blue = "#1686c4"
    green = "#0c8f5d"
    text = "根据阿姆达尔定律，若某部件优化后加速比为 5，\n但其仅影响 30% 的任务执行时间，则系统总加速比约为（ ）。"
    draw.multiline_text((28, 24), text, fill="#50665b", font=title_font, spacing=8)
    options = ["A. 1.15", "B. 1.25", "C. 1.32", "D. 1.45"]
    y = 128
    for option in options:
        draw.ellipse((32, y + 4, 58, y + 30), outline="#8aa89a", width=2)
        if option.startswith("D."):
            draw.ellipse((32, y + 4, 58, y + 30), fill="#88a296", outline="#88a296", width=2)
            draw.text((39, y + 4), "✓", fill="white", font=small_font)
        draw.text((82, y), option, fill="#52675d", font=body_font)
        y += 58
    draw.text((28, 380), "您的答案：D  ", fill="#52675d", font=small_font)
    draw.text((170, 380), "（答错了）", fill=red, font=small_font)
    draw.text((28, 420), "正确答案：C", fill=green, font=small_font)
    draw.text((28, 462), "解析：总加速比 = 1 / [(1 - 0.3) + (0.3 / 5)] = 1 / 0.76 ≈ 1.32", fill="#52675d", font=small_font)
    img.save(IMG_PATH)


def make_styles(font_name):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CnTitle", parent=styles["Title"], fontName=font_name, fontSize=20, leading=28, alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="CnH2", parent=styles["Heading2"], fontName=font_name, fontSize=14, leading=20, spaceBefore=9, spaceAfter=6, textColor=colors.HexColor("#1f2937")))
    styles.add(ParagraphStyle(name="CnBody", parent=styles["BodyText"], fontName=font_name, fontSize=10.2, leading=16, spaceAfter=5))
    styles.add(ParagraphStyle(name="CnBullet", parent=styles["BodyText"], fontName=font_name, fontSize=10.2, leading=16, leftIndent=12, firstLineIndent=-8, spaceAfter=3))
    styles.add(ParagraphStyle(name="CnCode", parent=styles["Code"], fontName=font_name, fontSize=9.2, leading=13, backColor=colors.HexColor("#f3f4f6"), borderColor=colors.HexColor("#e5e7eb"), borderWidth=0.5, borderPadding=5, spaceBefore=3, spaceAfter=6))
    return styles


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "")


def add_image(flowables, image_path):
    if not image_path.exists():
        return
    max_width = A4[0] - 32 * mm
    with Image.open(image_path) as img:
        width, height = img.size
    scale = min(max_width / width, 1)
    flowables.append(PdfImage(str(image_path), width=width * scale, height=height * scale))
    flowables.append(Spacer(1, 8))


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
        image_match = re.match(r"^!\[[^\]]*\]\(([^)]+)\)$", line.strip())
        if image_match and not in_code:
            flush_para()
            add_image(flowables, BASE_DIR / image_match.group(1))
            continue
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
        elif line.startswith("- "):
            flush_para()
            flowables.append(Paragraph("• " + escape(line[2:].strip()), styles["CnBullet"]))
        elif re.match(r"^\d+\.\s+", line):
            flush_para()
            flowables.append(Paragraph(escape(line), styles["CnBullet"]))
        elif not line.strip():
            flush_para()
            flowables.append(Spacer(1, 1))
        else:
            paragraph_lines.append(line)
    flush_para()
    flush_code()
    return flowables


def build_pdf():
    draw_question_image()
    font_name = register_font()
    styles = make_styles(font_name)
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="阿姆达尔定律加速比计算解题过程",
        author="Codex",
    )
    md_text = MD_PATH.read_text(encoding="utf-8")
    doc.build(markdown_to_flowables(md_text, styles))


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
