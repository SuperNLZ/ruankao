from html import escape
from pathlib import Path
import re

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


BASE_DIR = Path(__file__).resolve().parent
MD_PATH = BASE_DIR / "智慧医疗健康服务平台架构评估-快速记忆.md"
PDF_PATH = BASE_DIR / "智慧医疗健康服务平台架构评估-快速记忆.pdf"
IMG_DIR = BASE_DIR / "images"

FIG_BLANK = IMG_DIR / "智慧医疗健康服务平台架构评估-图1题图重绘.png"
FIG_ANSWER = IMG_DIR / "智慧医疗健康服务平台架构评估-图1效用树答案.png"

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


def draw_text_center(draw, box, text, font, fill=(30, 30, 30), line_gap=5):
    x1, y1, x2, y2 = box
    lines = wrap_text(text, font, x2 - x1 - 18)
    total_h = len(lines) * font.size + max(0, len(lines) - 1) * line_gap
    y = y1 + (y2 - y1 - total_h) / 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text((x1 + (x2 - x1 - w) / 2, y), line, font=font, fill=fill)
        y += font.size + line_gap


def draw_box(draw, box, text, font, fill=(255, 255, 255), outline=(50, 50, 50), text_fill=(25, 25, 25), width=3):
    draw.rectangle(box, fill=fill, outline=outline, width=width)
    draw_text_center(draw, box, text, font, text_fill)


def draw_arrow(draw, start, end, fill=(45, 45, 45), width=4):
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=fill, width=width)
    dx, dy = x2 - x1, y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    size = 14
    p1 = (x2 - ux * size + px * size * 0.45, y2 - uy * size + py * size * 0.45)
    p2 = (x2 - ux * size - px * size * 0.45, y2 - uy * size - py * size * 0.45)
    draw.polygon((end, p1, p2), fill=fill)


def make_utility_tree(path, answer=False):
    img = PILImage.new("RGB", (1100, 820), "white")
    draw = ImageDraw.Draw(img)
    title_font = load_font(30)
    font = load_font(24)
    small = load_font(18)
    leaf_font = load_font(19 if answer else 24)

    title = "图 1  智慧医疗健康服务平台效用树"
    if answer:
        title += "（答案版）"
    else:
        title += "（题图重绘）"
    draw.text((300, 25), title, font=title_font, fill=(20, 20, 20))

    root = (55, 350, 230, 445)
    trunk_x = 340
    attr_x1, attr_x2 = 440, 610
    leaf_x1, leaf_x2 = 780, 1010
    rows = [
        {
            "attr": "可修改性" if answer else "(1)",
            "leaves": ["(a) 医保政策变更\n3 人月适配", "(f) 新增功能\n2 周内集成"] if answer else ["(3)", "(f)"],
            "y": 140,
            "fill": (232, 246, 255),
        },
        {
            "attr": "可用性",
            "leaves": ["(b) 7x24 小时\n99.99%", "(g) 主库故障\n90 秒切换"] if answer else ["(b)", "(4)"],
            "y": 300,
            "fill": (232, 246, 232),
        },
        {
            "attr": "安全性",
            "leaves": ["(c) 检查报告\n不可篡改", "(e) 病历数据\n加密脱敏"] if answer else ["(c)", "(5)"],
            "y": 460,
            "fill": (255, 244, 230),
        },
        {
            "attr": "性能" if answer else "(2)",
            "leaves": ["(d) 高峰响应\n小于 1 秒", "(h) API 每天\n10000 次调用"] if answer else ["(6)", "(h)"],
            "y": 620,
            "fill": (245, 235, 255),
        },
    ]

    draw_box(draw, root, "质量效用", font, fill=(255, 255, 255))
    draw.line((root[2], (root[1] + root[3]) // 2, trunk_x, (root[1] + root[3]) // 2), fill=(45, 45, 45), width=4)
    draw.line((trunk_x, rows[0]["y"] + 45, trunk_x, rows[-1]["y"] + 45), fill=(45, 45, 45), width=4)

    for row in rows:
        y = row["y"]
        attr_box = (attr_x1, y, attr_x2, y + 90)
        draw_arrow(draw, (trunk_x, y + 45), (attr_x1, y + 45))
        draw_box(draw, attr_box, row["attr"], font, fill=row["fill"])

        mid_x = 690
        draw.line((attr_x2, y + 45, mid_x, y + 45), fill=(45, 45, 45), width=4)
        leaf_top = (leaf_x1, y - 38, leaf_x2, y + 28)
        leaf_bottom = (leaf_x1, y + 72, leaf_x2, y + 138)
        branch_x = 735
        draw.line((mid_x, y + 45, branch_x, y + 45), fill=(45, 45, 45), width=4)
        draw.line((branch_x, y - 5, branch_x, y + 105), fill=(45, 45, 45), width=4)
        draw_arrow(draw, (branch_x, y - 5), (leaf_x1, y - 5))
        draw_arrow(draw, (branch_x, y + 105), (leaf_x1, y + 105))
        draw_box(draw, leaf_top, row["leaves"][0], leaf_font, fill=(255, 255, 255), width=3)
        draw_box(draw, leaf_bottom, row["leaves"][1], leaf_font, fill=(255, 255, 255), width=3)

    note = "提示：本图根据用户提供截图重绘，用于复习和 PDF 嵌入。"
    draw.text((55, 770), note, font=small, fill=(90, 90, 90))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def ensure_images():
    make_utility_tree(FIG_BLANK, answer=False)
    make_utility_tree(FIG_ANSWER, answer=True)


def split_long_line(line, width=58):
    chunks = []
    current = ""
    for ch in line:
        current += ch
        if len(current) >= width:
            chunks.append(current)
            current = ""
    if current:
        chunks.append(current)
    return chunks or [""]


def normalize_inline(text):
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<font name='CN'>\1</font>", text)
    return text


def add_table(story, lines, style, font_name):
    rows = []
    for line in lines:
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if all(set(part) <= {"-", ":", " "} and "-" in part for part in parts):
            continue
        rows.append([Paragraph(normalize_inline(part), style) for part in parts])
    if not rows:
        return
    col_count = max(len(row) for row in rows)
    usable_width = A4[0] - 36 * mm
    table = Table(rows, colWidths=[usable_width / col_count] * col_count)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#b8c2cc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    story.append(Spacer(1, 5 * mm))


def add_image(story, rel_path):
    img_path = BASE_DIR / rel_path
    if not img_path.exists():
        return
    with PILImage.open(img_path) as img:
        width, height = img.size
    max_width = A4[0] - 36 * mm
    max_height = 145 * mm
    scale = min(max_width / width, max_height / height, 1)
    story.append(Image(str(img_path), width=width * scale, height=height * scale))
    story.append(Spacer(1, 5 * mm))


def build_pdf():
    ensure_images()
    font_name = register_font()
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    styles = {
        "h1": ParagraphStyle("h1", fontName=font_name, fontSize=20, leading=26, spaceAfter=8),
        "h2": ParagraphStyle("h2", fontName=font_name, fontSize=15, leading=21, spaceBefore=8, spaceAfter=5),
        "body": ParagraphStyle("body", fontName=font_name, fontSize=10.8, leading=17, spaceAfter=4),
        "code": ParagraphStyle("code", fontName=font_name, fontSize=9.5, leading=14, leftIndent=8, spaceAfter=4),
    }

    story = []
    lines = MD_PATH.read_text(encoding="utf-8").splitlines()
    in_code = False
    code_lines = []
    table_lines = []

    def flush_table():
        nonlocal table_lines
        if table_lines:
            add_table(story, table_lines, styles["body"], font_name)
            table_lines = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            wrapped = []
            for code_line in code_lines:
                wrapped.extend(split_long_line(code_line, 64))
            story.append(Preformatted("\n".join(wrapped), styles["code"]))
            story.append(Spacer(1, 3 * mm))
            code_lines = []

    for line in lines:
        if line.startswith("```"):
            flush_table()
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue

        if line.startswith("|"):
            table_lines.append(line)
            continue
        flush_table()

        image_match = re.match(r"!\[[^\]]*\]\(([^)]+)\)", line)
        if image_match:
            add_image(story, image_match.group(1))
            continue

        if not line.strip():
            story.append(Spacer(1, 2 * mm))
            continue

        if line.startswith("# "):
            story.append(Paragraph(normalize_inline(line[2:].strip()), styles["h1"]))
        elif line.startswith("## "):
            story.append(Paragraph(normalize_inline(line[3:].strip()), styles["h2"]))
        else:
            story.append(Paragraph(normalize_inline(line.strip()), styles["body"]))

    flush_table()
    if in_code:
        flush_code()

    doc.build(story)


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
