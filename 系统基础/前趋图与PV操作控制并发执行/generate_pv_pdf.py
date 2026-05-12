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
MD_PATH = BASE_DIR / "前趋图与PV操作控制并发执行解题过程.md"
PDF_PATH = BASE_DIR / "前趋图与PV操作控制并发执行解题过程.pdf"
IMG_DIR = BASE_DIR / "images"

QUESTION_IMG = IMG_DIR / "前趋图与PV操作控制并发执行-题目截图.png"
Q1_IMG = IMG_DIR / "前趋图与PV操作控制并发执行-问题1.png"
Q2_IMG = IMG_DIR / "前趋图与PV操作控制并发执行-问题2.png"
Q3_IMG = IMG_DIR / "前趋图与PV操作控制并发执行-问题3.png"

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


def draw_arrow(draw, start, end, fill=(35, 35, 35), width=3):
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=fill, width=width)
    dx, dy = x2 - x1, y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    size = 12
    p1 = (x2 - ux * size + px * size * 0.45, y2 - uy * size + py * size * 0.45)
    p2 = (x2 - ux * size - px * size * 0.45, y2 - uy * size - py * size * 0.45)
    draw.polygon((end, p1, p2), fill=fill)


def draw_node(draw, center, text, font):
    x, y = center
    r = 34
    draw.ellipse((x - r, y - r, x + r, y + r), outline=(30, 30, 30), width=3, fill=(255, 255, 255))
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((x - (bbox[2] - bbox[0]) / 2, y - (bbox[3] - bbox[1]) / 2 - 2), text, font=font, fill=(20, 20, 20))


def draw_code_block(draw, x, y, w, h, label, font):
    draw.rectangle((x, y, x + w, y + h), outline=(70, 70, 70), width=2, fill=(255, 255, 255))
    bbox = draw.textbbox((0, 0), label, font=font)
    draw.text((x + (w - (bbox[2] - bbox[0])) / 2, y + (h - (bbox[3] - bbox[1])) / 2 - 2), label, font=font, fill=(20, 20, 20))


def make_question_image(path):
    img = PILImage.new("RGB", (1500, 760), "white")
    draw = ImageDraw.Draw(img)
    text_font = load_font(25)
    small_font = load_font(22)
    code_font = load_font(22)

    prompt = (
        "进程P1、P2、P3、P4和P5的前趋图如下：\n"
        "若用PV操作控制进程P1~P5并发执行的过程，则需要设置6个信号S1、S2、S3、S4、S5和S6，"
        "且信号量S1~S6的初值都等于零。下图中a和b处应分别填写（问题1）；"
        "c和d处应分别填写（问题2）；e和f处应分别填写（问题3）。"
    )
    y = draw_wrapped(draw, prompt, (45, 28), text_font, 1400, gap=10)

    # Precedence graph.
    base_y = y + 35
    positions = {
        "P1": (150, base_y + 45),
        "P2": (150, base_y + 155),
        "P3": (305, base_y + 100),
        "P4": (500, base_y + 45),
        "P5": (500, base_y + 155),
    }
    edges = [
        ("P1", "P3"),
        ("P1", "P4"),
        ("P2", "P3"),
        ("P2", "P5"),
        ("P3", "P4"),
        ("P3", "P5"),
    ]
    for a, b in edges:
        draw_arrow(draw, positions[a], positions[b])
    for name, pos in positions.items():
        draw_node(draw, pos, name, small_font)
    draw.line((95, base_y - 15, 560, base_y - 15), fill=(20, 20, 20), width=2)

    # PV code layout.
    code_y = base_y + 260
    col_x = [85, 295, 545, 805, 1065]
    labels = ["P1", "P2", "P3", "P4", "P5"]
    for x, label in zip(col_x, labels):
        draw.text((x + 52, code_y - 35), label, font=small_font, fill=(20, 20, 20))

    # P1.
    draw.ellipse((col_x[0] + 62, code_y - 5, col_x[0] + 82, code_y + 15), outline=(20, 20, 20), width=2)
    draw_arrow(draw, (col_x[0] + 72, code_y + 15), (col_x[0] + 72, code_y + 120), width=2)
    draw.text((col_x[0] + 18, code_y + 45), "P1\n执行", font=small_font, fill=(20, 20, 20))
    draw_code_block(draw, col_x[0] + 15, code_y + 120, 115, 46, "a", code_font)

    # P2.
    draw.ellipse((col_x[1] + 62, code_y - 5, col_x[1] + 82, code_y + 15), outline=(20, 20, 20), width=2)
    draw_arrow(draw, (col_x[1] + 72, code_y + 15), (col_x[1] + 72, code_y + 120), width=2)
    draw.text((col_x[1] + 18, code_y + 45), "P2\n执行", font=small_font, fill=(20, 20, 20))
    draw_code_block(draw, col_x[1] + 15, code_y + 120, 115, 46, "b", code_font)

    # P3.
    draw_code_block(draw, col_x[2] + 5, code_y - 10, 130, 46, "c", code_font)
    draw_arrow(draw, (col_x[2] + 70, code_y + 36), (col_x[2] + 70, code_y + 120), width=2)
    draw.text((col_x[2] + 18, code_y + 57), "P3\n执行", font=small_font, fill=(20, 20, 20))
    draw_code_block(draw, col_x[2] + 5, code_y + 120, 130, 46, "d", code_font)

    # P4.
    draw_code_block(draw, col_x[3] + 5, code_y - 10, 130, 46, "e", code_font)
    draw_arrow(draw, (col_x[3] + 70, code_y + 36), (col_x[3] + 70, code_y + 158), width=2)
    draw.text((col_x[3] + 18, code_y + 72), "P4\n执行", font=small_font, fill=(20, 20, 20))
    draw.ellipse((col_x[3] + 60, code_y + 158, col_x[3] + 80, code_y + 178), outline=(20, 20, 20), width=2)

    # P5.
    draw_code_block(draw, col_x[4] + 5, code_y - 10, 130, 46, "f", code_font)
    draw_arrow(draw, (col_x[4] + 70, code_y + 36), (col_x[4] + 70, code_y + 158), width=2)
    draw.text((col_x[4] + 18, code_y + 72), "P5\n执行", font=small_font, fill=(20, 20, 20))
    draw.ellipse((col_x[4] + 60, code_y + 158, col_x[4] + 80, code_y + 178), outline=(20, 20, 20), width=2)

    draw.text((45, 700), "说明：本图根据用户截图内容重绘，便于嵌入PDF复习。", font=load_font(18), fill=(90, 90, 90))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def make_option_image(path, question_title, options, correct, chosen=None):
    height = 92 + 58 * len(options) + (110 if chosen else 30)
    img = PILImage.new("RGB", (700, height), "white")
    draw = ImageDraw.Draw(img)
    title_font = load_font(24)
    text_font = load_font(24)
    small_font = load_font(21)

    draw.rounded_rectangle((28, 16, 168, 52), radius=7, outline=(255, 90, 90), width=2)
    draw.text((40, 22), question_title, font=small_font, fill=(255, 90, 90))

    y = 80
    for letter, text in options:
        is_correct = letter == correct
        color = (16, 185, 129) if is_correct else (20, 20, 20)
        border = (16, 185, 129) if is_correct else (160, 160, 160)
        draw.rectangle((34, y, 66, y + 36), outline=border, width=2, fill=(255, 255, 255))
        draw.text((43, y + 4), letter, font=small_font, fill=border)
        draw.text((86, y + 3), text, font=text_font, fill=color)
        y += 58

    if chosen:
        draw.line((0, y + 4, 700, y + 4), fill=(230, 230, 230), width=2)
        draw.text((34, y + 28), "答案", font=title_font, fill=(20, 20, 20))
        draw.text((34, y + 75), f"正确答案：{correct}", font=text_font, fill=(20, 20, 20))
        draw.text((34, y + 118), f"你的答案：{chosen}", font=text_font, fill=(20, 20, 20))

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def ensure_images():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    make_question_image(QUESTION_IMG)
    make_option_image(
        Q1_IMG,
        "问题1 [单选题]",
        [
            ("A", "P(S1) P(S2) 和 P(S3) P(S4)"),
            ("B", "P(S1) V(S2) 和 P(S2) V(S1)"),
            ("C", "V(S1) V(S2) 和 V(S3) V(S4)"),
            ("D", "P(S1) P(S2) 和 V(S1) V(S2)"),
        ],
        correct="C",
        chosen="B",
    )
    make_option_image(
        Q2_IMG,
        "问题2 [单选题]",
        [
            ("A", "P(S1) P(S2) 和 V(S3) V(S4)"),
            ("B", "P(S1) P(S3) 和 V(S5) V(S6)"),
            ("C", "V(S1) V(S2) 和 P(S3) P(S4)"),
            ("D", "P(S1) V(S3) 和 P(S2) V(S4)"),
        ],
        correct="B",
    )
    make_option_image(
        Q3_IMG,
        "问题3 [单选题]",
        [
            ("A", "P(S3) P(S4) 和 V(S5) V(S6)"),
            ("B", "V(S5) V(S6) 和 P(S5) P(S6)"),
            ("C", "P(S2) P(S5) 和 P(S4) P(S6)"),
            ("D", "P(S4) V(S5) 和 P(S5) V(S6)"),
        ],
        correct="C",
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
        title="前趋图与PV操作控制并发执行解题过程",
        author="Codex",
    )
    md_text = MD_PATH.read_text(encoding="utf-8")
    flowables = markdown_to_flowables(md_text, styles, doc.width)
    doc.build(flowables)


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
