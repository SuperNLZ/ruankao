from pathlib import Path
import re

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


BASE_DIR = Path(__file__).resolve().parent
MD_PATH = BASE_DIR / "索引节点地址转换解题过程.md"
PDF_PATH = BASE_DIR / "索引节点地址转换解题过程.pdf"
IMG_DIR = BASE_DIR / "images"
QUESTION_IMG = IMG_DIR / "索引节点地址转换-题目截图.png"
ANSWER_IMG = IMG_DIR / "索引节点地址转换-参考答案截图.png"

FONT_PATHS = [
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
]


def pick_font_path():
    for font_path in FONT_PATHS:
        if font_path.exists():
            return font_path
    return None


def load_pil_font(size):
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


def draw_wrapped(draw, text, xy, font, fill, max_width, line_gap=8):
    x, y = xy
    for line in wrap_text(text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


def draw_arrow(draw, start, end, fill=(40, 40, 40), width=3):
    draw.line([start, end], fill=fill, width=width)
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    size = 12
    p1 = (x2 - ux * size + px * size * 0.5, y2 - uy * size + py * size * 0.5)
    p2 = (x2 - ux * size - px * size * 0.5, y2 - uy * size - py * size * 0.5)
    draw.polygon([end, p1, p2], fill=fill)


def draw_block(draw, x, y, w, row_h, values, font, title=None):
    if title:
        draw.text((x, y - 32), title, font=font, fill=(70, 70, 70))
    h = row_h * len(values)
    draw.rectangle((x, y, x + w, y + h), outline=(30, 30, 30), width=2, fill=(255, 255, 255))
    for idx, value in enumerate(values):
        yy = y + idx * row_h
        if idx > 0:
            draw.line((x, yy, x + w, yy), fill=(30, 30, 30), width=1)
        if value:
            draw.text((x + 16, yy + 8), value, font=font, fill=(30, 30, 30))
            draw.ellipse((x + w - 26, yy + 16, x + w - 14, yy + 28), fill=(30, 30, 30))
    return (x, y, x + w, y + h)


def draw_data_box(draw, x, y):
    draw.rectangle((x, y, x + 34, y + 34), outline=(30, 30, 30), width=2, fill=(255, 255, 255))
    return (x, y + 17)


def make_question_image(path):
    img = PILImage.new("RGB", (1700, 900), "white")
    draw = ImageDraw.Draw(img)
    title_font = load_pil_font(32)
    text_font = load_pil_font(24)
    small_font = load_pil_font(20)

    question = (
        "假设文件系统采用索引节点管理，目录索引节点有8个地址项iaddr[0]~iaddr[7]，"
        "每个地址项大小为4字节。iaddr[0]~iaddr[4]采用直接地址索引，"
        "iaddr[5]和iaddr[6]采用一级间接地址索引，iaddr[7]采用二级间接地址索引。"
        "假设磁盘索引块和磁盘数据块大小均为1KB字节，文件File1的索引节点如图所示。"
        "若用户访问文件File1中逻辑块号为5和261的信息，则对应的物理块号分别为（ ）；"
        "101号物理块存放的是（ ）。"
    )
    y = draw_wrapped(draw, question, (40, 32), text_font, (20, 20, 20), 1620, 7)

    y += 30
    draw.text((40, y), "索引节点示意图（按题图内容重绘）", font=title_font, fill=(20, 20, 20))
    y += 55

    left_x, top_y = 70, y + 20
    label_x = 48
    row_h = 56
    values = ["50", "67", "68", "78", "89", "90", "91", "101"]
    labels = [f"iaddr[{i}]" for i in range(8)]
    block = draw_block(draw, left_x + 110, top_y, 94, row_h, values, text_font)
    for idx, label in enumerate(labels):
        draw.text((label_x, top_y + idx * row_h + 12), label, font=small_font, fill=(30, 30, 30))

    # Direct blocks.
    data_x = 380
    for idx in range(5):
        start = (block[2] - 18, top_y + idx * row_h + 28)
        end = draw_data_box(draw, data_x, top_y + idx * row_h + 11)
        draw_arrow(draw, start, end)
    draw.text((340, top_y + 5 * row_h + 12), "直接索引", font=small_font, fill=(80, 80, 80))

    # First-level indirect blocks for iaddr[5] and iaddr[6].
    b90 = draw_block(draw, 520, top_y + 10, 120, 48, ["58", "59", "...", "136"], text_font, "一级索引块")
    b91 = draw_block(draw, 520, top_y + 250, 120, 48, ["187", "193", "...", "129"], text_font, "一级索引块")
    draw_arrow(draw, (block[2] - 18, top_y + 5 * row_h + 28), (b90[0], b90[1] + 24))
    draw_arrow(draw, (block[2] - 18, top_y + 6 * row_h + 28), (b91[0], b91[1] + 24))
    for i, yy in enumerate([b90[1] + 7, b90[1] + 55, b90[1] + 151, b91[1] + 7, b91[1] + 55, b91[1] + 151]):
        end = draw_data_box(draw, 705, yy)
        sx = 640
        sy = yy + 17
        draw_arrow(draw, (sx, sy), end)

    # Second-level indirect address.
    b101 = draw_block(draw, 340, top_y + 455, 125, 58, ["156", "...", "168"], text_font, "二级索引块")
    draw_arrow(draw, (block[2] - 18, top_y + 7 * row_h + 28), (b101[0], b101[1] + 29))

    b156 = draw_block(draw, 590, top_y + 430, 135, 52, ["261", "...", "516"], text_font, "一级索引块")
    b168 = draw_block(draw, 590, top_y + 610, 135, 52, ["518", "...", "1021"], text_font, "一级索引块")
    draw_arrow(draw, (b101[2] - 18, b101[1] + 29), (b156[0], b156[1] + 26))
    draw_arrow(draw, (b101[2] - 18, b101[1] + 145), (b168[0], b168[1] + 26))
    for yy in [b156[1] + 9, b156[1] + 113, b168[1] + 9, b168[1] + 113]:
        end = draw_data_box(draw, 790, yy)
        draw_arrow(draw, (725, yy + 17), end)

    note = (
        "关键定位：逻辑块5是iaddr[5]一级间接索引块中的第1项，指向物理块58；"
        "逻辑块261是iaddr[6]一级间接索引块中的第1项，指向物理块187；"
        "iaddr[7]=101表示101号物理块保存二级间接索引表。"
    )
    draw_wrapped(draw, note, (910, top_y + 55), text_font, (20, 20, 20), 720, 10)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def make_answer_image(path):
    img = PILImage.new("RGB", (1700, 520), "white")
    draw = ImageDraw.Draw(img)
    title_font = load_pil_font(32)
    text_font = load_pil_font(25)
    draw.text((40, 30), "解析", font=title_font, fill=(20, 20, 20))
    answer = (
        "根据题意，磁盘索引块为1KB，每个地址项大小为4B，故每个磁盘索引块可存放1024/4=256个物理块地址。"
        "又因为文件索引节点中有8个地址项，其中5个地址项为直接地址索引，这意味着逻辑块号为0~4的为直接地址索引；"
        "2个地址项是一级间接地址索引，其中第一个地址项指出的物理块中是一张一级间接地址索引表，"
        "存放逻辑块号为5~260对应的物理块号，第二个地址项指出的物理块中是另一张一级间接地址索引表，"
        "存放逻辑块号为261~516对应的物理块号。经上述分析，逻辑块号为5的信息应该存放在58号物理块中，"
        "逻辑块号为261的信息应该存放在187号物理块中。\n\n"
        "由题中可知，iaddr[7]采用二级间接地址索引，且iaddr[7]中存放的物理块号为101。"
        "1个地址项是二级间接地址索引，这意味着该地址项指出的物理块中存放的是256个一级间接地址索引表，"
        "故101号物理块存放的是二级间接地址索引表。"
    )
    draw_wrapped(draw, answer, (40, 90), text_font, (20, 20, 20), 1620, 12)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def ensure_assets():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    if not QUESTION_IMG.exists():
        make_question_image(QUESTION_IMG)
    if not ANSWER_IMG.exists():
        make_answer_image(ANSWER_IMG)


def register_fonts():
    font_path = pick_font_path()
    if font_path:
        pdfmetrics.registerFont(TTFont("CN", str(font_path)))
        return "CN"
    return "Helvetica"


def make_styles(font_name):
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CnTitle",
            parent=styles["Title"],
            fontName=font_name,
            fontSize=22,
            leading=30,
            alignment=TA_CENTER,
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CnH2",
            parent=styles["Heading2"],
            fontName=font_name,
            fontSize=15,
            leading=22,
            textColor=colors.HexColor("#1f2937"),
            spaceBefore=10,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CnH3",
            parent=styles["Heading3"],
            fontName=font_name,
            fontSize=12.5,
            leading=18,
            textColor=colors.HexColor("#374151"),
            spaceBefore=8,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CnBody",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=10.5,
            leading=17,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CnBullet",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=10.5,
            leading=17,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CnCode",
            parent=styles["Code"],
            fontName=font_name,
            fontSize=9.5,
            leading=14,
            backColor=colors.HexColor("#f3f4f6"),
            borderColor=colors.HexColor("#e5e7eb"),
            borderWidth=0.6,
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=8,
        )
    )
    return styles


def escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("`", "")
    )


def markdown_to_flowables(md_text, styles, doc_width):
    flowables = []
    paragraph_lines = []
    code_lines = []
    in_code = False

    def flush_para():
        nonlocal paragraph_lines
        if paragraph_lines:
            text = " ".join(line.strip() for line in paragraph_lines)
            flowables.append(Paragraph(escape(text), styles["CnBody"]))
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
            continue
        if line.startswith("## "):
            flush_para()
            flowables.append(Paragraph(escape(line[3:].strip()), styles["CnH2"]))
            continue
        if line.startswith("### "):
            flush_para()
            flowables.append(Paragraph(escape(line[4:].strip()), styles["CnH3"]))
            continue
        if line.startswith("- "):
            flush_para()
            flowables.append(Paragraph("• " + escape(line[2:].strip()), styles["CnBullet"]))
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)", line)
        if numbered:
            flush_para()
            flowables.append(
                Paragraph(f"{numbered.group(1)}. {escape(numbered.group(2).strip())}", styles["CnBullet"])
            )
            continue
        if not line.strip():
            flush_para()
            continue

        paragraph_lines.append(line)

    flush_para()
    flush_code()
    return flowables


def build_pdf():
    ensure_assets()
    font_name = register_fonts()
    styles = make_styles(font_name)
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="索引节点地址转换解题过程",
        author="Codex",
    )
    md_text = MD_PATH.read_text(encoding="utf-8")
    flowables = markdown_to_flowables(md_text, styles, doc.width)
    doc.build(flowables)


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
