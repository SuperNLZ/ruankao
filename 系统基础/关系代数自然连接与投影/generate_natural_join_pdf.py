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
MD_PATH = BASE_DIR / "关系代数自然连接与投影解题过程.md"
PDF_PATH = BASE_DIR / "关系代数自然连接与投影解题过程.pdf"
IMG_PATH = BASE_DIR / "images" / "关系代数自然连接与投影-题目截图.png"

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


def draw_table(draw, x, y, headers, rows, title, font, small_font):
    cell_w = 78
    cell_h = 40
    draw.text((x + cell_w, y - 34), title, fill="#222222", font=font)
    all_rows = [headers] + rows
    for r, row in enumerate(all_rows):
        for c, value in enumerate(row):
            left = x + c * cell_w
            top = y + r * cell_h
            draw.rectangle((left, top, left + cell_w, top + cell_h), outline="#333333", width=2)
            draw.text((left + 27, top + 8), str(value), fill="#111111", font=small_font)


def draw_question_image():
    IMG_PATH.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1000, 900), "#d8eee1")
    draw = ImageDraw.Draw(img)
    title_font = pil_font(24)
    body_font = pil_font(22)
    small_font = pil_font(20)
    red = "#cc3333"
    green = "#0c8f5d"
    draw.text((28, 22), "第 10/36 题：单选题", fill="#50665b", font=title_font)
    question = "若关系 R、S 如下图所示，则关系 R 与 S 进行自然连接运算后的\n元组个数和属性列数分别为（ ）。"
    draw.multiline_text((28, 66), question, fill="#222222", font=body_font, spacing=8)
    draw_table(
        draw,
        96,
        150,
        ["A", "B", "C", "D"],
        [[6, 3, 1, 5], [6, 1, 5, 1], [6, 5, 7, 4], [6, 3, 7, 4]],
        "R",
        body_font,
        small_font,
    )
    draw_table(draw, 610, 150, ["C", "D"], [[1, 5], [7, 4]], "S", body_font, small_font)
    opts = ["A. 6 和 6", "B. 4 和 6", "C. 3 和 6", "D. 3 和 4"]
    y = 390
    for option in opts:
        draw.ellipse((38, y + 4, 64, y + 30), outline="#8aa89a", width=2)
        if option.startswith("B."):
            draw.ellipse((38, y + 4, 64, y + 30), fill="#88a296", outline="#88a296", width=2)
            draw.text((45, y + 4), "✓", fill="white", font=small_font)
        draw.text((88, y), option, fill="#52675d", font=body_font)
        y += 58
    draw.text((28, 650), "您的答案：B  ", fill="#52675d", font=small_font)
    draw.text((170, 650), "（答错了）", fill=red, font=small_font)
    draw.text((28, 690), "正确答案：D", fill=green, font=small_font)
    explain = "解析：自然连接按同名属性 C、D 相等匹配，并去掉重复同名列。\nR 中匹配 S 的 C、D 为 (1,5)、(7,4)、(7,4)，所以 3 个元组；\n结果属性为 A、B、C、D，所以 4 列。"
    draw.multiline_text((28, 730), explain, fill="#52675d", font=small_font, spacing=8)
    img.save(IMG_PATH)


def make_styles(font_name):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CnTitle", parent=styles["Title"], fontName=font_name, fontSize=20, leading=28, alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="CnH2", parent=styles["Heading2"], fontName=font_name, fontSize=14, leading=20, spaceBefore=9, spaceAfter=6, textColor=colors.HexColor("#1f2937")))
    styles.add(ParagraphStyle(name="CnBody", parent=styles["BodyText"], fontName=font_name, fontSize=10.0, leading=15.5, spaceAfter=5))
    styles.add(ParagraphStyle(name="CnBullet", parent=styles["BodyText"], fontName=font_name, fontSize=10.0, leading=15.5, leftIndent=12, firstLineIndent=-8, spaceAfter=3))
    styles.add(ParagraphStyle(name="CnCode", parent=styles["Code"], fontName=font_name, fontSize=8.8, leading=12.5, backColor=colors.HexColor("#f3f4f6"), borderColor=colors.HexColor("#e5e7eb"), borderWidth=0.5, borderPadding=5, spaceBefore=3, spaceAfter=6))
    return styles


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "")


def add_image(flowables, image_path):
    if not image_path.exists():
        return
    max_width = A4[0] - 32 * mm
    max_height = 105 * mm
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
        title="关系代数自然连接与投影解题过程",
        author="Codex",
    )
    md_text = MD_PATH.read_text(encoding="utf-8")
    doc.build(markdown_to_flowables(md_text, styles))


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
