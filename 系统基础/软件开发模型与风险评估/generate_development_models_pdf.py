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
DOCUMENTS = [
    (
        BASE_DIR / "软件开发模型与风险评估-概念讲解.md",
        BASE_DIR / "软件开发模型与风险评估-概念讲解.pdf",
        "软件开发模型与风险评估-概念讲解",
    ),
    (
        BASE_DIR / "软件开发模型与风险评估-快速记忆.md",
        BASE_DIR / "软件开发模型与风险评估-快速记忆.pdf",
        "软件开发模型与风险评估-快速记忆",
    ),
]
IMG_DIR = BASE_DIR / "images"
KNOWLEDGE_IMG = IMG_DIR / "软件开发模型与风险评估-知识点截图.png"

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


def draw_wrapped(draw, text, xy, font, max_width, fill=(20, 20, 20), gap=9):
    x, y = xy
    for line in wrap_text(text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + gap
    return y


def make_knowledge_image(path):
    img = PILImage.new("RGB", (1500, 430), "white")
    draw = ImageDraw.Draw(img)
    font = load_font(23)
    blue = (37, 99, 235)
    gray = (95, 105, 120)

    y = 24
    y = draw_wrapped(draw, "本题考察的是软件开发模型中的特点，尤其是如何考虑风险评估问题。", (28, y), font, 1430, gray, 9)
    y += 18
    items = [
        ("A选项 瀑布模型：", "瀑布模型（Waterfall Model）是一种传统的线性开发模型，它遵循严格的阶段顺序，通常不涉及风险评估。它的缺点是对需求变化适应性差，容易在开发后期暴露风险，但它本身没有增加专门的风险评估环节。"),
        ("B选项 螺旋模型：", "螺旋模型结合了迭代和原型开发的特点，重点在于风险评估。它每个开发周期都包括了风险评估的环节，通过分析每个阶段的潜在风险，确保开发过程中能够及时调整。这使得螺旋模型成为强调风险管理和控制的开发模式。"),
        ("C选项 V模型：", "V模型（Verification and Validation Model）侧重于每个开发阶段后紧随相应的验证和确认过程，确保质量控制，但它并未特别增加风险评估环节。"),
        ("D选项 增量模型：", "增量模型通过分阶段交付产品的功能，但它不强调风险评估，而是侧重于逐步交付和反馈。"),
    ]
    for prefix, rest in items:
        draw.text((28, y), prefix, font=font, fill=blue)
        prefix_width = int(font.getlength(prefix))
        y = draw_wrapped(draw, rest, (28 + prefix_width, y), font, 1430 - prefix_width, gray, 9)
        y += 13
    draw_wrapped(draw, "因此，选项B螺旋模型增加了风险评估环节，所以答案是B。", (28, y), font, 1430, gray, 9)

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def ensure_images():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    make_knowledge_image(KNOWLEDGE_IMG)


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
    ensure_images()
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
    doc.build(markdown_to_flowables(md_text, styles, doc.width))


if __name__ == "__main__":
    for md_path, pdf_path, title in DOCUMENTS:
        build_pdf(md_path, pdf_path, title)
        print(pdf_path)
