from pathlib import Path
import re
import math

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
MD_PATH = BASE_DIR / "CacheAside缓存策略数据一致性解题过程.md"
PDF_PATH = BASE_DIR / "CacheAside缓存策略数据一致性解题过程.pdf"
IMG_DIR = BASE_DIR / "images"
READ_IMG = IMG_DIR / "图1数据读取模块.png"
UPDATE_IMG = IMG_DIR / "图2数据更新模块.png"

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


def draw_center(draw, box, text, font, fill=(20, 20, 20)):
    x1, y1, x2, y2 = box
    lines = str(text).split("\n")
    line_h = font.size + 7
    total_h = line_h * len(lines) - 7
    y = y1 + (y2 - y1 - total_h) / 2
    for line in lines:
        w, h = text_size(draw, line, font)
        draw.text((x1 + (x2 - x1 - w) / 2, y), line, font=font, fill=fill)
        y += line_h


def arrow(draw, start, end, fill=(20, 20, 20), width=3, dashed=False):
    x1, y1 = start
    x2, y2 = end
    if dashed:
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        dash = 14
        gap = 8
        if dist == 0:
            return
        ux = dx / dist
        uy = dy / dist
        pos = 0
        while pos < dist:
            seg_start = pos
            seg_end = min(pos + dash, dist)
            draw.line(
                (
                    x1 + ux * seg_start,
                    y1 + uy * seg_start,
                    x1 + ux * seg_end,
                    y1 + uy * seg_end,
                ),
                fill=fill,
                width=width,
            )
            pos += dash + gap
    else:
        draw.line((x1, y1, x2, y2), fill=fill, width=width)

    angle = math.atan2(y2 - y1, x2 - x1)
    size = 13
    p1 = (x2, y2)
    p2 = (x2 - size * math.cos(angle - math.pi / 6), y2 - size * math.sin(angle - math.pi / 6))
    p3 = (x2 - size * math.cos(angle + math.pi / 6), y2 - size * math.sin(angle + math.pi / 6))
    draw.polygon([p1, p2, p3], fill=fill)


def draw_box(draw, box, label, font, fill="#ffffff"):
    draw.rounded_rectangle(box, radius=2, fill=fill, outline="#111827", width=3)
    draw_center(draw, box, label, font)


def draw_diamond(draw, center, size, label, font, fill="#ffffff"):
    cx, cy = center
    w, h = size
    points = [(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)]
    draw.polygon(points, fill=fill, outline="#111827")
    draw.line(points + [points[0]], fill="#111827", width=3)
    draw_center(draw, (cx - w / 2 + 8, cy - h / 2 + 8, cx + w / 2 - 8, cy + h / 2 - 8), label, font)


def draw_cylinder(draw, box, label, font, fill="#ffffff"):
    x1, y1, x2, y2 = box
    ellipse_h = 24
    draw.rectangle((x1, y1 + ellipse_h / 2, x2, y2 - ellipse_h / 2), fill=fill, outline="#111827", width=3)
    draw.ellipse((x1, y1, x2, y1 + ellipse_h), fill=fill, outline="#111827", width=3)
    draw.arc((x1, y2 - ellipse_h, x2, y2), 0, 180, fill="#111827", width=3)
    draw.line((x1, y1 + ellipse_h / 2, x1, y2 - ellipse_h / 2), fill="#111827", width=3)
    draw.line((x2, y1 + ellipse_h / 2, x2, y2 - ellipse_h / 2), fill="#111827", width=3)
    draw_center(draw, box, label, font)


def label(draw, xy, text, font, fill="#111827"):
    x, y = xy
    w, h = text_size(draw, text, font)
    pad_x, pad_y = 9, 5
    draw.rounded_rectangle(
        (x - pad_x, y - pad_y, x + w + pad_x, y + h + pad_y),
        radius=5,
        fill="#ffffff",
        outline="#d1d5db",
        width=1,
    )
    draw.text((x, y), text, font=font, fill=fill)


def make_read_image():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    width, height = 980, 560
    img = PILImage.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    title_font = load_font(31)
    node_font = load_font(28)
    label_font = load_font(25)
    caption_font = load_font(23)

    draw_center(draw, (0, 22, width, 68), "Cache-Aside 数据读取模块", title_font)

    read_box = (65, 235, 205, 325)
    cache_center = (470, 280)
    cache_size = (150, 120)
    db_box = (735, 215, 870, 345)

    draw_box(draw, read_box, "读请求", node_font)
    draw_diamond(draw, cache_center, cache_size, "缓存", node_font)
    draw_cylinder(draw, db_box, "数据库", node_font)

    # (1) 读请求访问缓存。
    arrow(draw, (205, 280), (395, 280))
    label(draw, (290, 242), "(1)", label_font)

    # (2) 缓存命中后返回。
    arrow(draw, (470, 220), (135, 220))
    arrow(draw, (135, 220), (135, 235))
    label(draw, (300, 180), "(2)", label_font)

    # (3) 缓存未命中后查询数据库。
    arrow(draw, (545, 280), (735, 280))
    label(draw, (620, 242), "(3)", label_font)

    # (4) 数据库结果回填缓存。
    arrow(draw, (740, 345), (505, 338), dashed=True)
    arrow(draw, (505, 338), (485, 340), dashed=True)
    label(draw, (615, 365), "(4)", label_font)

    # (5) 数据库查询结果返回给请求。
    arrow(draw, (760, 345), (760, 430))
    arrow(draw, (760, 430), (135, 430))
    arrow(draw, (135, 430), (135, 325))
    label(draw, (415, 445), "(5)", label_font)

    draw_center(draw, (0, 500, width, 538), "图1 数据库缓存系统中的数据读取模块的设计方案", caption_font)
    img.save(READ_IMG)


def make_update_image():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    width, height = 900, 300
    img = PILImage.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    title_font = load_font(30)
    node_font = load_font(27)
    label_font = load_font(24)
    caption_font = load_font(22)

    draw_center(draw, (0, 18, width, 58), "Cache-Aside 数据更新模块", title_font)

    write_box = (70, 122, 205, 205)
    db_box = (380, 96, 515, 226)
    cache_center = (720, 160)
    cache_size = (150, 110)

    draw_box(draw, write_box, "写请求", node_font)
    draw_cylinder(draw, db_box, "数据库", node_font)
    draw_diamond(draw, cache_center, cache_size, "缓存", node_font)

    arrow(draw, (205, 163), (380, 163))
    label(draw, (282, 126), "(1)", label_font)
    arrow(draw, (515, 163), (645, 163))
    label(draw, (575, 126), "(2)", label_font)

    draw_center(draw, (0, 258, width, 292), "图2 数据库缓存系统中的数据更新模块的设计方案", caption_font)
    img.save(UPDATE_IMG)


def make_images():
    make_read_image()
    make_update_image()


def make_styles(font_name):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CnTitle", parent=styles["Title"], fontName=font_name, fontSize=20, leading=28, alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="CnH2", parent=styles["Heading2"], fontName=font_name, fontSize=14, leading=20, spaceBefore=9, spaceAfter=6, textColor=colors.HexColor("#1f2937")))
    styles.add(ParagraphStyle(name="CnH3", parent=styles["Heading3"], fontName=font_name, fontSize=11.5, leading=17, spaceBefore=6, spaceAfter=4, textColor=colors.HexColor("#374151")))
    styles.add(ParagraphStyle(name="CnH4", parent=styles["Heading4"], fontName=font_name, fontSize=10.5, leading=15, spaceBefore=5, spaceAfter=3, textColor=colors.HexColor("#4b5563")))
    styles.add(ParagraphStyle(name="CnBody", parent=styles["BodyText"], fontName=font_name, fontSize=9.6, leading=15, spaceAfter=5))
    styles.add(ParagraphStyle(name="CnBullet", parent=styles["BodyText"], fontName=font_name, fontSize=9.6, leading=15, leftIndent=12, firstLineIndent=-8, spaceAfter=3))
    styles.add(ParagraphStyle(name="CnCode", parent=styles["Code"], fontName=font_name, fontSize=8.6, leading=12, backColor=colors.HexColor("#f3f4f6"), borderColor=colors.HexColor("#e5e7eb"), borderWidth=0.5, borderPadding=5, spaceBefore=3, spaceAfter=6))
    return styles


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "")


def flush_paragraph(flowables, paragraph_lines, style):
    if paragraph_lines:
        text = " ".join(line.strip() for line in paragraph_lines)
        flowables.append(Paragraph(escape(text), style))
        paragraph_lines.clear()


def flush_block(flowables, lines, style):
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
                flush_block(flowables, code_lines, styles["CnCode"])
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
                render_w = min(doc_width, w * 0.55)
                render_h = h * render_w / w
                flowables.append(Image(str(image_path), width=render_w, height=render_h))
                flowables.append(Spacer(1, 8))
            else:
                flowables.append(Paragraph(f"图片缺失：{escape(str(image_path))}", styles["CnBody"]))
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
        if line.startswith("#### "):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Paragraph(escape(line[5:].strip()), styles["CnH4"]))
            continue
        if line.startswith("- "):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Paragraph("• " + escape(line[2:].strip()), styles["CnBullet"]))
            continue
        if re.match(r"^\d+\.\s+", line):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Paragraph(escape(line), styles["CnBullet"]))
            continue
        if not line.strip():
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Spacer(1, 1))
            continue

        paragraph_lines.append(line)

    flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
    flush_block(flowables, code_lines, styles["CnCode"])
    return flowables


def build_pdf():
    make_images()
    font_name = register_font()
    styles = make_styles(font_name)
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Cache-Aside 缓存策略数据一致性解题过程",
        author="Codex",
    )
    md_text = MD_PATH.read_text(encoding="utf-8")
    doc.build(markdown_to_flowables(md_text, styles, doc.width))


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
