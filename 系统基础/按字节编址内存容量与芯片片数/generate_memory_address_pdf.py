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
MD_PATH = BASE_DIR / "按字节编址内存容量与芯片片数解题过程.md"
PDF_PATH = BASE_DIR / "按字节编址内存容量与芯片片数解题过程.pdf"
IMG_DIR = BASE_DIR / "images"

QUESTION_IMG = IMG_DIR / "按字节编址内存容量与芯片片数-题目截图.png"
Q1_IMG = IMG_DIR / "按字节编址内存容量与芯片片数-问题1.png"
Q2_IMG = IMG_DIR / "按字节编址内存容量与芯片片数-问题2.png"

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


def wrap_text(text, font, max_width):
    lines = []
    current = ""
    for ch in text:
        if ch == "\n":
            lines.append(current)
            current = ""
            continue
        trial = current + ch
        if font.getlength(trial) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, text, xy, font, max_width, fill=(20, 20, 20), gap=8):
    x, y = xy
    for line in wrap_text(text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + gap
    return y


def make_question_image(path):
    img = PILImage.new("RGB", (1450, 180), "white")
    draw = ImageDraw.Draw(img)
    font = load_font(26)
    text = (
        "内存按字节编址，地址从A0000H到CFFFFH的内存，共有（ ）字节，"
        "若用存储容量为64k*8bit的存储器芯片构成该内存空间，至少需要（ ）片。"
    )
    draw_wrapped(draw, text, (25, 58), font, 1380)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def make_option_image(path, title, options, correct, chosen=None):
    height = 92 + 58 * len(options) + 118 + (42 if chosen else 0)
    img = PILImage.new("RGB", (540, height), "white")
    draw = ImageDraw.Draw(img)
    title_font = load_font(22)
    text_font = load_font(24)

    draw.rounded_rectangle((28, 16, 175, 52), radius=7, outline=(255, 90, 90), width=2)
    draw.text((39, 22), title, font=title_font, fill=(255, 90, 90))

    y = 82
    for letter, text in options:
        is_correct = letter == correct
        is_chosen_wrong = chosen == letter and chosen != correct
        color = (16, 185, 129) if is_correct else ((255, 90, 90) if is_chosen_wrong else (20, 20, 20))
        border = (16, 185, 129) if is_correct else ((255, 90, 90) if is_chosen_wrong else (160, 160, 160))
        draw.rectangle((34, y, 66, y + 36), outline=border, width=2, fill=(255, 255, 255))
        draw.text((43, y + 4), letter, font=title_font, fill=border)
        draw.text((86, y + 3), text, font=text_font, fill=color)
        y += 58

    draw.line((0, y + 4, 540, y + 4), fill=(230, 230, 230), width=2)
    draw.text((34, y + 28), "答案", font=title_font, fill=(20, 20, 20))
    draw.text((34, y + 75), f"正确答案：{correct}", font=text_font, fill=(20, 20, 20))
    if chosen:
        draw.text((34, y + 118), f"你的答案：{chosen}", font=text_font, fill=(20, 20, 20))

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def ensure_images():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    make_question_image(QUESTION_IMG)
    make_option_image(
        Q1_IMG,
        "问题1 [单选题]",
        [("A", "80k"), ("B", "96k"), ("C", "160k"), ("D", "192k")],
        correct="D",
        chosen="B",
    )
    make_option_image(
        Q2_IMG,
        "问题2 [单选题]",
        [("A", "2"), ("B", "3"), ("C", "5"), ("D", "8")],
        correct="B",
    )


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
                w, h = pil_img.size
                render_w = doc_width
                render_h = h * render_w / w
                flowables.append(Image(str(image_path), width=render_w, height=render_h))
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
        elif line.startswith("### "):
            flush_para()
            flowables.append(Paragraph(escape(line[4:].strip()), styles["CnH3"]))
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


def build_pdf():
    ensure_images()
    font_name = register_font()
    styles = make_styles(font_name)
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="按字节编址内存容量与芯片片数解题过程",
        author="Codex",
    )
    md_text = MD_PATH.read_text(encoding="utf-8")
    flowables = markdown_to_flowables(md_text, styles, doc.width)
    doc.build(flowables)


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
