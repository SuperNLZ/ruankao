from pathlib import Path
import math
import re

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, Preformatted, SimpleDocTemplate, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


BASE_DIR = Path(__file__).resolve().parent
MD_PATH = BASE_DIR / "解释器体系结构风格-快速记忆.md"
PDF_PATH = BASE_DIR / "解释器体系结构风格-快速记忆.pdf"
IMG_DIR = BASE_DIR / "images"
DIAGRAM_PATH = IMG_DIR / "解释器体系结构风格简图.png"

FONT_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
]


def pick_font_path():
    for font_path in FONT_CANDIDATES:
        if font_path.exists():
            return font_path
    return None


def load_font(size):
    font_path = pick_font_path()
    if font_path:
        return ImageFont.truetype(str(font_path), size=size)
    return ImageFont.load_default()


def register_font():
    font_path = pick_font_path()
    if font_path:
        pdfmetrics.registerFont(TTFont("CN", str(font_path)))
        return "CN"
    return "Helvetica"


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_center(draw, box, text, font, fill=(32, 45, 64)):
    x1, y1, x2, y2 = box
    lines = str(text).split("\n")
    line_h = font.size + 7
    total_h = line_h * len(lines) - 7
    y = y1 + (y2 - y1 - total_h) / 2
    for line in lines:
        w, _ = text_size(draw, line, font)
        draw.text((x1 + (x2 - x1 - w) / 2, y), line, font=font, fill=fill)
        y += line_h


def arrow(draw, start, end, fill=(37, 99, 235), width=4):
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=fill, width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 15
    p1 = (x2, y2)
    p2 = (x2 - size * math.cos(angle - math.pi / 6), y2 - size * math.sin(angle - math.pi / 6))
    p3 = (x2 - size * math.cos(angle + math.pi / 6), y2 - size * math.sin(angle + math.pi / 6))
    draw.polygon([p1, p2, p3], fill=fill)


def draw_box(draw, box, text, font, fill="#eff6ff"):
    draw.rounded_rectangle(box, radius=8, fill=fill, outline="#2563eb", width=3)
    draw_center(draw, box, text, font)


def draw_circle(draw, center, radius, text, font, fill="#f0fdf4"):
    cx, cy = center
    box = (cx - radius, cy - radius, cx + radius, cy + radius)
    draw.ellipse(box, fill=fill, outline="#16a34a", width=3)
    draw_center(draw, box, text, font)


def draw_label(draw, pos, text, font, fill=(17, 24, 39)):
    x, y = pos
    w, h = text_size(draw, text, font)
    draw.rounded_rectangle((x - 8, y - 5, x + w + 8, y + h + 5), radius=5, fill="white", outline="#d1d5db")
    draw.text((x, y), text, font=font, fill=fill)


def make_diagram():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    img = PILImage.new("RGB", (1120, 720), "white")
    draw = ImageDraw.Draw(img)
    title_font = load_font(34)
    node_font = load_font(27)
    small_font = load_font(22)
    caption_font = load_font(25)

    draw_center(draw, (0, 22, 1120, 70), "解释器体系结构风格快速记忆图", title_font)

    box1 = (190, 205, 455, 335)
    box_program = (720, 165, 1010, 310)
    box2 = (740, 430, 990, 560)
    circle3_center = (300, 505)

    draw_box(draw, box1, "1\n程序执行的\n当前状态", node_font)
    draw_box(draw, box_program, "被解释执行\n的程序", node_font, fill="#f8fafc")
    draw_box(draw, box2, "2\n解释器引擎的\n内部状态", node_font)
    draw_circle(draw, circle3_center, 95, "3\n解释器引擎", node_font)

    draw_label(draw, (55, 250), "输入", small_font)
    arrow(draw, (125, 265), (190, 265))

    draw_label(draw, (60, 520), "输出", small_font)
    arrow(draw, (205, 505), (120, 520))

    draw_label(draw, (60, 405), "计算状态机", small_font)
    arrow(draw, (170, 425), (230, 455))

    draw_label(draw, (500, 455), "选择的指令\n选择的数据", small_font)
    arrow(draw, (740, 495), (395, 500))

    draw_label(draw, (620, 595), "获取/存储", small_font)
    arrow(draw, (450, 585), (385, 540))

    draw_label(draw, (500, 95), "存储器", small_font)
    arrow(draw, (560, 130), (410, 205))
    arrow(draw, (620, 130), (740, 430))
    arrow(draw, (645, 130), (780, 165))

    arrow(draw, (720, 310), (865, 430))
    arrow(draw, (455, 285), (740, 465))
    arrow(draw, (300, 410), (300, 335))
    arrow(draw, (340, 335), (340, 415))

    draw_center(draw, (0, 655, 1120, 700), "口诀：左状态，右内存，下引擎", caption_font)
    img.save(DIAGRAM_PATH)


def make_styles(font_name):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CnTitle", parent=styles["Title"], fontName=font_name, fontSize=20, leading=28, alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="CnH2", parent=styles["Heading2"], fontName=font_name, fontSize=14, leading=20, spaceBefore=8, spaceAfter=5, textColor=colors.HexColor("#1f2937")))
    styles.add(ParagraphStyle(name="CnH3", parent=styles["Heading3"], fontName=font_name, fontSize=11.5, leading=16, spaceBefore=5, spaceAfter=3, textColor=colors.HexColor("#374151")))
    styles.add(ParagraphStyle(name="CnBody", parent=styles["BodyText"], fontName=font_name, fontSize=9.5, leading=14.5, spaceAfter=4))
    styles.add(ParagraphStyle(name="CnBullet", parent=styles["BodyText"], fontName=font_name, fontSize=9.5, leading=14.5, leftIndent=12, firstLineIndent=-8, spaceAfter=3))
    styles.add(ParagraphStyle(name="CnCode", parent=styles["Code"], fontName=font_name, fontSize=8.5, leading=12, backColor=colors.HexColor("#f3f4f6"), borderColor=colors.HexColor("#e5e7eb"), borderWidth=0.5, borderPadding=5, spaceBefore=3, spaceAfter=6))
    return styles


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "")


def flush_paragraph(flowables, lines, style):
    if lines:
        flowables.append(Paragraph(escape(" ".join(line.strip() for line in lines)), style))
        lines.clear()


def flush_code(flowables, lines, style):
    if lines:
        flowables.append(Preformatted("\n".join(lines), style))
        lines.clear()


def markdown_to_flowables(md_text, styles, doc_width):
    flowables = []
    paragraph_lines = []
    code_lines = []
    in_code = False

    for raw_line in md_text.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            if in_code:
                flush_code(flowables, code_lines, styles["CnCode"])
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        image_match = re.match(r"!\[(.*?)\]\((.*?)\)", line)
        if image_match:
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            image_path = (BASE_DIR / image_match.group(2)).resolve()
            if image_path.exists():
                pil_img = PILImage.open(image_path)
                w, h = pil_img.size
                render_w = min(doc_width, w * 0.42)
                render_h = h * render_w / w
                flowables.append(Image(str(image_path), width=render_w, height=render_h))
                flowables.append(Spacer(1, 8))
            continue

        if line.startswith("# "):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Paragraph(escape(line[2:].strip()), styles["CnTitle"]))
            continue
        if line.startswith("## "):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Paragraph(escape(line[3:].strip()), styles["CnH2"]))
            continue
        if line.startswith("### "):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Paragraph(escape(line[4:].strip()), styles["CnH3"]))
            continue
        if line.startswith("- "):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Paragraph("• " + escape(line[2:].strip()), styles["CnBullet"]))
            continue
        if not line.strip():
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Spacer(1, 1))
            continue

        paragraph_lines.append(line)

    flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
    flush_code(flowables, code_lines, styles["CnCode"])
    return flowables


def build_pdf():
    make_diagram()
    font_name = register_font()
    styles = make_styles(font_name)
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="解释器体系结构风格-快速记忆",
        author="Codex",
    )
    md_text = MD_PATH.read_text(encoding="utf-8")
    doc.build(markdown_to_flowables(md_text, styles, doc.width))


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
