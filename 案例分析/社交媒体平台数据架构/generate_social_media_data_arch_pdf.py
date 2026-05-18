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
MD_PATH = BASE_DIR / "社交媒体平台数据架构-解题过程.md"
PDF_PATH = BASE_DIR / "社交媒体平台数据架构-解题过程.pdf"
IMG_DIR = BASE_DIR / "images"
TABLE_IMG = IMG_DIR / "社交媒体平台数据架构-题目表格.png"

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


def make_table_image():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    img = PILImage.new("RGB", (1320, 260), "white")
    draw = ImageDraw.Draw(img)
    header_font = load_font(30)
    body_font = load_font(28)
    small_font = load_font(22)

    x0, y0 = 12, 12
    widths = [220, 470, 590]
    heights = [56, 50, 50, 50, 50]
    xs = [x0]
    for width in widths:
        xs.append(xs[-1] + width)
    ys = [y0]
    for height in heights:
        ys.append(ys[-1] + height)

    for row in range(len(heights)):
        for col in range(len(widths)):
            fill = (230, 230, 230) if row == 0 else (255, 255, 255)
            draw.rectangle((xs[col], ys[row], xs[col + 1], ys[row + 1]), outline=(0, 0, 0), width=2, fill=fill)

    cells = [
        ["特性", "数据仓库", "数据湖"],
        ["数据类型", "结构化数据为主", "（1）"],
        ["数据处理", "（2）", "实时处理"],
        ["查询延迟", "低", "（3）"],
        ["适用场景", "（4）", "探索性分析、AI 训练、多源数据整合"],
    ]

    for row, line in enumerate(cells):
        for col, text in enumerate(line):
            font = header_font if row == 0 else body_font
            if row == 4 and col == 2:
                font = small_font
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = xs[col] + (widths[col] - tw) / 2
            y = ys[row] + (heights[row] - th) / 2 - 2
            draw.text((x, y), text, font=font, fill=(0, 0, 0))

    img.save(TABLE_IMG)


def make_styles(font_name):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CnTitle", parent=styles["Title"], fontName=font_name, fontSize=20, leading=28, alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="CnH2", parent=styles["Heading2"], fontName=font_name, fontSize=14, leading=20, spaceBefore=9, spaceAfter=6, textColor=colors.HexColor("#1f2937")))
    styles.add(ParagraphStyle(name="CnH3", parent=styles["Heading3"], fontName=font_name, fontSize=11.5, leading=17, spaceBefore=6, spaceAfter=4, textColor=colors.HexColor("#374151")))
    styles.add(ParagraphStyle(name="CnBody", parent=styles["BodyText"], fontName=font_name, fontSize=9.6, leading=15, spaceAfter=5))
    styles.add(ParagraphStyle(name="CnBullet", parent=styles["BodyText"], fontName=font_name, fontSize=9.6, leading=15, leftIndent=12, firstLineIndent=-8, spaceAfter=3))
    styles.add(ParagraphStyle(name="CnCode", parent=styles["Code"], fontName=font_name, fontSize=8.6, leading=12, backColor=colors.HexColor("#f3f4f6"), borderColor=colors.HexColor("#e5e7eb"), borderWidth=0.5, borderPadding=5, spaceBefore=3, spaceAfter=6))
    styles.add(ParagraphStyle(name="CnTable", parent=styles["Code"], fontName=font_name, fontSize=8.0, leading=11, backColor=colors.HexColor("#ffffff"), borderColor=colors.HexColor("#e5e7eb"), borderWidth=0.5, borderPadding=5, spaceBefore=3, spaceAfter=6))
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
    table_lines = []
    in_code = False

    for raw_line in md_text.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flush_block(flowables, table_lines, styles["CnTable"])
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
            flush_block(flowables, table_lines, styles["CnTable"])
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

        if line.startswith("|"):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            table_lines.append(line)
            continue
        else:
            flush_block(flowables, table_lines, styles["CnTable"])

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
    flush_block(flowables, table_lines, styles["CnTable"])
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
        title="社交媒体平台数据架构-解题过程",
        author="Codex",
    )
    md_text = MD_PATH.read_text(encoding="utf-8")
    doc.build(markdown_to_flowables(md_text, styles, doc.width))


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
