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
MD_PATH = BASE_DIR / "医疗管理系统数据流图解题过程.md"
PDF_PATH = BASE_DIR / "医疗管理系统数据流图解题过程.pdf"
IMG_DIR = BASE_DIR / "images"
FIG1 = IMG_DIR / "医疗管理系统数据流图-图1-1上下文图.png"
FIG2 = IMG_DIR / "医疗管理系统数据流图-图1-2零层图.png"

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


def draw_wrapped(draw, text, xy, font, max_width, fill=(20, 20, 20), gap=5):
    x, y = xy
    for line in wrap_text(text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + gap
    return y


def draw_box(draw, xy, label, font, fill=(255, 255, 255)):
    x1, y1, x2, y2 = xy
    draw.rectangle(xy, outline=(40, 40, 40), width=2, fill=fill)
    lines = label.split("\n")
    total_h = len(lines) * (font.size + 3)
    y = y1 + ((y2 - y1) - total_h) / 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        draw.text((x1 + ((x2 - x1) - (bbox[2] - bbox[0])) / 2, y), line, font=font, fill=(20, 20, 20))
        y += font.size + 3


def draw_process(draw, xy, label, font):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=16, outline=(40, 40, 40), width=2, fill=(250, 250, 250))
    lines = label.split("\n")
    total_h = len(lines) * (font.size + 3)
    y = y1 + ((y2 - y1) - total_h) / 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        draw.text((x1 + ((x2 - x1) - (bbox[2] - bbox[0])) / 2, y), line, font=font, fill=(20, 20, 20))
        y += font.size + 3


def draw_store(draw, xy, label, font):
    x1, y1, x2, y2 = xy
    draw.rectangle(xy, outline=(40, 40, 40), width=2, fill=(255, 255, 245))
    draw.line((x1, y1, x1, y2), fill=(40, 40, 40), width=5)
    bbox = draw.textbbox((0, 0), label, font=font)
    draw.text((x1 + ((x2 - x1) - (bbox[2] - bbox[0])) / 2, y1 + ((y2 - y1) - (bbox[3] - bbox[1])) / 2), label, font=font, fill=(20, 20, 20))


def draw_arrow(draw, start, end, label, font, label_pos=None):
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=(35, 35, 35), width=2)
    dx, dy = x2 - x1, y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    size = 10
    p1 = (x2 - ux * size + px * size * 0.45, y2 - uy * size + py * size * 0.45)
    p2 = (x2 - ux * size - px * size * 0.45, y2 - uy * size - py * size * 0.45)
    draw.polygon((end, p1, p2), fill=(35, 35, 35))
    if label:
        lx, ly = label_pos if label_pos else ((x1 + x2) / 2, (y1 + y2) / 2)
        draw_wrapped(draw, label, (lx, ly), font, 180, fill=(20, 20, 20), gap=2)


def make_context_image(path):
    img = PILImage.new("RGB", (1200, 660), "white")
    draw = ImageDraw.Draw(img)
    title_font = load_font(28)
    font = load_font(19)
    small = load_font(16)
    draw.text((36, 28), "图1-1 上下文数据流图（按题图内容重绘）", font=title_font, fill=(20, 20, 20))

    draw_box(draw, (70, 160, 190, 230), "E1\n客户", font)
    draw_box(draw, (70, 410, 190, 480), "E2\n医生", font)
    draw_box(draw, (980, 155, 1100, 225), "E3\n主管", font)
    draw_process(draw, (500, 265, 700, 375), "医疗管理系统", title_font)

    draw_arrow(draw, (190, 175), (500, 285), "通用信息查询请求", small, (250, 155))
    draw_arrow(draw, (190, 205), (500, 320), "预约请求/\n预约查询请求", small, (250, 235))
    draw_arrow(draw, (500, 350), (190, 455), "预约所需数据/\n通用信息查询结果/\n预约反馈", small, (230, 370))

    draw_arrow(draw, (190, 420), (500, 345), "应聘请求/辞职请求\n出诊时间/处方", small, (245, 435))
    draw_arrow(draw, (500, 375), (190, 475), "聘用反馈/解聘反馈\n预约通知/药品已开出反馈", small, (230, 510))

    draw_arrow(draw, (700, 285), (980, 180), "医生应聘申请/\n医生辞职申请/\n报表", small, (760, 135))
    draw_arrow(draw, (980, 210), (700, 320), "医生应聘批复/\n医生辞职批复", small, (760, 225))
    draw_arrow(draw, (980, 225), (700, 350), "报表查询请求", small, (800, 360))

    draw.text((36, 600), "说明：聊天截图无法直接落盘，本文档使用复习用重绘图。", font=small, fill=(100, 100, 100))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def make_level0_image(path):
    img = PILImage.new("RGB", (1500, 1050), "white")
    draw = ImageDraw.Draw(img)
    title_font = load_font(28)
    font = load_font(17)
    small = load_font(14)
    red = (185, 28, 28)
    draw.text((36, 28), "图1-2 0层数据流图（按题图内容重绘，红字为缺失数据流）", font=title_font, fill=(20, 20, 20))

    # External entities
    draw_box(draw, (50, 210, 145, 270), "E1\n客户", font)
    draw_box(draw, (50, 600, 145, 660), "E2\n医生", font)
    draw_box(draw, (1250, 90, 1360, 155), "E3\n主管", font)

    # Processes
    draw_process(draw, (260, 110, 420, 175), "P1\n通用信息查询", font)
    draw_process(draw, (260, 660, 420, 725), "P2\n医生聘用", font)
    draw_process(draw, (310, 360, 470, 430), "P3\n预约处理", font)
    draw_process(draw, (1040, 650, 1200, 725), "P4\n药品管理", font)
    draw_process(draw, (850, 360, 1015, 430), "P5\n报表创建", font)

    # Stores
    draw_store(draw, (530, 135, 700, 185), "D1 通用信息表", small)
    draw_store(draw, (600, 470, 780, 520), "D2 预约表", small)
    draw_store(draw, (570, 650, 750, 700), "D3 医生表", small)
    draw_store(draw, (580, 295, 800, 345), "D4 医生出诊时间表", small)
    draw_store(draw, (1220, 505, 1400, 555), "D5 药品数据", small)

    # Normal flows
    draw_arrow(draw, (145, 225), (260, 130), "通用信息查询请求", small, (145, 150))
    draw_arrow(draw, (260, 160), (145, 255), "通用信息查询结果", small, (145, 285))
    draw_arrow(draw, (420, 130), (530, 150), "查询通用信息", small, (430, 100))
    draw_arrow(draw, (530, 175), (420, 160), "相关通用信息", small, (430, 190))

    draw_arrow(draw, (145, 245), (310, 380), "预约请求/\n预约查询请求", small, (160, 330))
    draw_arrow(draw, (310, 415), (145, 255), "预约所需数据/\n预约反馈", small, (140, 430))
    draw_arrow(draw, (145, 610), (310, 410), "出诊时间", small, (190, 540))
    draw_arrow(draw, (470, 410), (145, 610), "预约通知", small, (260, 570))
    draw_arrow(draw, (750, 650), (470, 415), "在职医生列表", small, (520, 585))
    draw_arrow(draw, (580, 320), (470, 380), "所需出诊时间", small, (485, 305))
    draw_arrow(draw, (470, 405), (600, 485), "新增的预约", small, (500, 475))

    draw_arrow(draw, (145, 615), (260, 675), "应聘请求/\n辞职请求", small, (150, 690))
    draw_arrow(draw, (260, 710), (145, 645), "聘用反馈/\n解聘反馈", small, (155, 745))
    draw_arrow(draw, (420, 700), (570, 680), "更新的医生列表", small, (430, 710))
    draw_arrow(draw, (1250, 130), (420, 675), "医生应聘批复/\n医生辞职批复", small, (520, 735))
    draw_arrow(draw, (420, 660), (1250, 120), "医生应聘申请/\n医生辞职申请", small, (585, 780))

    draw_arrow(draw, (145, 640), (1040, 700), "处方", small, (900, 740))
    draw_arrow(draw, (1040, 685), (145, 640), "药品已开出反馈", small, (1030, 780))
    draw_arrow(draw, (1200, 665), (1220, 535), "药品名称", small, (1125, 575))
    draw_arrow(draw, (1200, 700), (1220, 545), "更新的药品库存信息", small, (1110, 615))

    draw_arrow(draw, (700, 160), (850, 375), "通用信息", small, (750, 205))
    draw_arrow(draw, (780, 500), (850, 405), "预约数据", small, (770, 450))
    draw_arrow(draw, (800, 320), (850, 380), "出诊时间", small, (790, 350))
    draw_arrow(draw, (750, 675), (850, 415), "医生信息", small, (770, 600))
    draw_arrow(draw, (1220, 520), (1015, 405), "药品库存数据", small, (1050, 470))
    draw_arrow(draw, (1250, 140), (1015, 380), "报表查询请求", small, (1060, 250))
    draw_arrow(draw, (1015, 395), (1250, 120), "报表", small, (1120, 170))

    # Missing flows highlighted
    draw.line((470, 380, 580, 305), fill=red, width=4)
    draw.text((475, 255), "缺失：更新的出诊时间\nP3 -> D4", font=small, fill=red)
    draw.line((420, 665, 580, 340), fill=red, width=4)
    draw.text((430, 535), "缺失：删除的医生出诊安排\nP2 -> D4", font=small, fill=red)
    draw.line((1220, 545, 1200, 675), fill=red, width=4)
    draw.text((1210, 575), "缺失：药品库存信息\nD5 -> P4", font=small, fill=red)
    draw.line((1040, 675, 780, 505), fill=red, width=4)
    draw.text((815, 555), "缺失：治疗信息\nP4 -> D2", font=small, fill=red)

    draw.text((36, 1000), "说明：红色数据流为问题3需要补充的核心缺失项。", font=small, fill=(100, 100, 100))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def ensure_images():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    make_context_image(FIG1)
    make_level0_image(FIG2)


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
        elif line.startswith("## "):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Paragraph(escape(line[3:].strip()), styles["CnH2"]))
        elif line.startswith("### "):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Paragraph(escape(line[4:].strip()), styles["CnH3"]))
        elif line.startswith("- "):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Paragraph("• " + escape(line[2:].strip()), styles["CnBullet"]))
        elif re.match(r"^\d+\.\s+", line):
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Paragraph(escape(line), styles["CnBullet"]))
        elif not line.strip():
            flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
            flowables.append(Spacer(1, 1))
        else:
            paragraph_lines.append(line)

    flush_paragraph(flowables, paragraph_lines, styles["CnBody"])
    flush_block(flowables, table_lines, styles["CnTable"])
    flush_block(flowables, code_lines, styles["CnCode"])
    return flowables


def build_pdf():
    ensure_images()
    font_name = register_font()
    styles = make_styles(font_name)
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="医疗管理系统数据流图解题过程",
        author="Codex",
    )
    md_text = MD_PATH.read_text(encoding="utf-8")
    doc.build(markdown_to_flowables(md_text, styles, doc.width))


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
