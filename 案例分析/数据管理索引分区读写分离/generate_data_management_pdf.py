from pathlib import Path
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
MD_PATH = BASE_DIR / "数据管理索引分区读写分离解题过程.md"
PDF_PATH = BASE_DIR / "数据管理索引分区读写分离解题过程.pdf"
IMG_DIR = BASE_DIR / "images"
TABLE_IMG = IMG_DIR / "表4-1物理分区模式比较表.png"

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


def draw_center(draw, box, text, font, fill=(20, 20, 20)):
    x1, y1, x2, y2 = box
    lines = str(text).split("\n")
    line_h = font.size + 5
    total_h = line_h * len(lines) - 5
    y = y1 + (y2 - y1 - total_h) / 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text((x1 + (x2 - x1 - w) / 2, y), line, font=font, fill=fill)
        y += line_h


def make_table_image():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    width, height = 1460, 355
    img = PILImage.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    title_font = load_font(30)
    header_font = load_font(26)
    cell_font = load_font(25)

    draw_center(draw, (0, 8, width, 52), "表4-1 物理分区模式比较表", title_font)

    left, top = 10, 58
    col_widths = [190, 310, 360, 310, 280]
    row_heights = [58, 58, 58, 58, 58]
    headers = ["分区模式", "分区依据", "适合数据", "数据管理能力", "数据分布"]
    rows = [
        ["范围分区", "属性取值范围", "（b）", "能力强", "不均匀"],
        ["哈希分区", "（a）", "静态数据", "能力弱", "均匀"],
        ["列表分区", "属性的离散值", "单属性、离散值", "能力强", "（d）"],
        ["组合分区", "属性组合分区", "周期、离散等", "（c）", "\\"],
    ]

    x_positions = [left]
    for w in col_widths:
        x_positions.append(x_positions[-1] + w)
    y_positions = [top]
    for h in row_heights:
        y_positions.append(y_positions[-1] + h)

    for y in y_positions:
        draw.line((left, y, x_positions[-1], y), fill=(0, 0, 0), width=2)
    for x in x_positions:
        draw.line((x, top, x, y_positions[-1]), fill=(0, 0, 0), width=2)

    for c, header in enumerate(headers):
        draw_center(draw, (x_positions[c], y_positions[0], x_positions[c + 1], y_positions[1]), header, header_font)

    for r, row in enumerate(rows, start=1):
        for c, text in enumerate(row):
            draw_center(draw, (x_positions[c], y_positions[r], x_positions[c + 1], y_positions[r + 1]), text, cell_font)

    img.save(TABLE_IMG)


def make_styles(font_name):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CnTitle", parent=styles["Title"], fontName=font_name, fontSize=20, leading=28, alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="CnH2", parent=styles["Heading2"], fontName=font_name, fontSize=14, leading=20, spaceBefore=9, spaceAfter=6, textColor=colors.HexColor("#1f2937")))
    styles.add(ParagraphStyle(name="CnH3", parent=styles["Heading3"], fontName=font_name, fontSize=11.5, leading=17, spaceBefore=6, spaceAfter=4, textColor=colors.HexColor("#374151")))
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
                render_w = doc_width
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
    make_table_image()
    font_name = register_font()
    styles = make_styles(font_name)
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="数据管理索引分区读写分离解题过程",
        author="Codex",
    )
    md_text = MD_PATH.read_text(encoding="utf-8")
    doc.build(markdown_to_flowables(md_text, styles, doc.width))


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
