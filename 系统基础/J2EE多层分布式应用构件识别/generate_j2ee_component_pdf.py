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
MD_PATH = BASE_DIR / "J2EE多层分布式应用构件识别解题过程.md"
PDF_PATH = BASE_DIR / "J2EE多层分布式应用构件识别解题过程.pdf"
IMG_PATH = BASE_DIR / "images" / "J2EE多层分布式应用构件识别-题目截图.png"

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


def draw_box(draw, box, label, font, fill="#ffffff", outline="#333333"):
    draw.rectangle(box, fill=fill, outline=outline, width=2)
    x1, y1, x2, y2 = box
    lines = label.split("\n")
    total_h = len(lines) * 24
    y = y1 + (y2 - y1 - total_h) / 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text((x1 + (x2 - x1 - w) / 2, y), line, fill="#111111", font=font)
        y += 24


def arrow(draw, start, end):
    draw.line((start, end), fill="#111111", width=3)
    ex, ey = end
    sx, sy = start
    if ex >= sx:
        points = [(ex, ey), (ex - 10, ey - 6), (ex - 10, ey + 6)]
    else:
        points = [(ex, ey), (ex + 10, ey - 6), (ex + 10, ey + 6)]
    draw.polygon(points, fill="#111111")


def draw_question_image():
    IMG_PATH.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1200, 720), "#d8eee1")
    draw = ImageDraw.Draw(img)
    title_font = pil_font(24)
    font = pil_font(20)
    small = pil_font(18)
    red = "#cc3333"
    green = "#0c8f5d"

    draw.text((22, 18), "第 28/28 题：单选题", fill="#52675d", font=title_font)
    question = "J2EE 平台采用多层分布式应用程序模型，不同构件部署在不同层次。\n图中靠近 DB 的 (5) 应识别为哪类构件？"
    draw.multiline_text((22, 58), question, fill="#52675d", font=font, spacing=8)

    # Diagram frame
    y0 = 130
    draw_box(draw, (40, y0, 250, y0 + 190), "客户端", small, "#ffffff")
    draw_box(draw, (270, y0, 480, y0 + 190), "Web", small, "#ffffff")
    draw_box(draw, (500, y0, 830, y0 + 190), "(3)\nEJB 容器/服务器", small, "#ffffff")
    draw_box(draw, (850, y0, 1030, y0 + 190), "DB", small, "#ffffff")

    draw_box(draw, (72, y0 + 42, 218, y0 + 85), "浏览器", small)
    draw_box(draw, (75, y0 + 105, 150, y0 + 145), "HTML", small)
    draw_box(draw, (160, y0 + 105, 225, y0 + 145), "(1)", small, "#fff8e1")

    draw_box(draw, (300, y0 + 42, 450, y0 + 85), "Web服务器", small)
    draw_box(draw, (305, y0 + 105, 370, y0 + 145), "JSP", small)
    draw_box(draw, (382, y0 + 105, 445, y0 + 145), "(2)", small, "#fff8e1")

    draw_box(draw, (535, y0 + 50, 650, y0 + 150), "Simple\nBean", small)
    draw_box(draw, (535, y0 + 115, 650, y0 + 160), "(4)", small, "#fff8e1")
    draw_box(draw, (690, y0 + 50, 800, y0 + 150), "(5)", small, "#fff8e1")
    draw.ellipse((902, y0 + 55, 978, y0 + 82), outline="#333333", width=2)
    draw.rectangle((902, y0 + 68, 978, y0 + 132), outline="#333333", width=2)
    draw.ellipse((902, y0 + 118, 978, y0 + 145), outline="#333333", width=2)

    arrow(draw, (225, y0 + 126), (305, y0 + 126))
    arrow(draw, (445, y0 + 126), (535, y0 + 126))
    arrow(draw, (650, y0 + 100), (690, y0 + 100))
    arrow(draw, (800, y0 + 100), (902, y0 + 100))

    opts = ["A. Applet", "B. Servlet", "C. EntityBean", "D. SessionBean"]
    y = 370
    for option in opts:
        draw.ellipse((42, y + 3, 68, y + 29), outline="#8aa89a", width=2)
        if option.startswith("B."):
            draw.ellipse((42, y + 3, 68, y + 29), fill="#88a296", outline="#88a296", width=2)
            draw.text((49, y + 2), "✓", fill="white", font=small)
        draw.text((92, y), option, fill="#52675d", font=font)
        y += 56

    draw.text((22, 612), "您的答案：B  ", fill="#52675d", font=small)
    draw.text((160, 612), "（答错了）", fill=red, font=small)
    draw.text((22, 650), "正确答案：C", fill=green, font=small)
    img.save(IMG_PATH)


def make_styles(font_name):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CnTitle", parent=styles["Title"], fontName=font_name, fontSize=20, leading=28, alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="CnH2", parent=styles["Heading2"], fontName=font_name, fontSize=14, leading=20, spaceBefore=9, spaceAfter=6, textColor=colors.HexColor("#1f2937")))
    styles.add(ParagraphStyle(name="CnBody", parent=styles["BodyText"], fontName=font_name, fontSize=10.2, leading=16, spaceAfter=5))
    styles.add(ParagraphStyle(name="CnBullet", parent=styles["BodyText"], fontName=font_name, fontSize=10.2, leading=16, leftIndent=12, firstLineIndent=-8, spaceAfter=3))
    styles.add(ParagraphStyle(name="CnCode", parent=styles["Code"], fontName=font_name, fontSize=9.0, leading=12.8, backColor=colors.HexColor("#f3f4f6"), borderColor=colors.HexColor("#e5e7eb"), borderWidth=0.5, borderPadding=5, spaceBefore=3, spaceAfter=6))
    return styles


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "")


def add_image(flowables, image_path):
    if not image_path.exists():
        return
    max_width = A4[0] - 32 * mm
    max_height = 100 * mm
    with Image.open(image_path) as img:
        width, height = img.size
    scale = min(max_width / width, max_height / height, 1)
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
        title="J2EE多层分布式应用构件识别解题过程",
        author="Codex",
    )
    md_text = MD_PATH.read_text(encoding="utf-8")
    doc.build(markdown_to_flowables(md_text, styles))


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
