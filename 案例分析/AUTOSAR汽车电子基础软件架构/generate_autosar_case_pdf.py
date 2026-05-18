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
MD_PATH = BASE_DIR / "AUTOSAR汽车电子基础软件架构-快速记忆.md"
PDF_PATH = BASE_DIR / "AUTOSAR汽车电子基础软件架构-快速记忆.pdf"
IMG_DIR = BASE_DIR / "images"

FIG_31 = IMG_DIR / "AUTOSAR汽车电子基础软件架构-图3-1.png"
FIG_32 = IMG_DIR / "AUTOSAR汽车电子基础软件架构-图3-2.png"
FIG_33 = IMG_DIR / "AUTOSAR汽车电子基础软件架构-图3-3.png"
FIG_34 = IMG_DIR / "AUTOSAR汽车电子基础软件架构-图3-4.png"

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


def draw_text_center(draw, box, text, font, fill=(20, 20, 20), line_gap=4):
    x1, y1, x2, y2 = box
    lines = wrap_text(text, font, x2 - x1 - 12)
    total_h = len(lines) * font.size + max(0, len(lines) - 1) * line_gap
    y = y1 + (y2 - y1 - total_h) / 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text((x1 + (x2 - x1 - w) / 2, y), line, font=font, fill=fill)
        y += font.size + line_gap


def draw_box(draw, box, text, font, fill=(255, 255, 255), outline=(50, 50, 50), text_fill=(20, 20, 20), width=2):
    draw.rectangle(box, fill=fill, outline=outline, width=width)
    draw_text_center(draw, box, text, font, fill=text_fill)


def draw_arrow(draw, start, end, fill=(45, 45, 45), width=3):
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


def make_fig_31(path):
    img = PILImage.new("RGB", (1300, 780), "white")
    draw = ImageDraw.Draw(img)
    title_font = load_font(28)
    font = load_font(21)
    small = load_font(17)
    gray = (232, 236, 240)
    blue = (226, 240, 255)

    draw.text((390, 25), "图 3-1  AUTOSAR 定义的工作包", font=title_font, fill=(20, 20, 20))
    draw_box(draw, (500, 80, 800, 125), "工作包", font, fill=(245, 245, 245))

    columns = [
        ("II-1\n系统架构", ["软件架构", "汽车和系统\n约束分析", "需求管理", "增强功能\n数据描述", "方法论和\n流程"], gray),
        ("II-2\n软件和通讯规范", ["基础软件", "通信栈", "FlexRay", "诊断", "操作系统\n规范"], gray),
        ("II-3\n验证", ["基础软件\n验证", "方法论验证"], (255, 255, 255)),
        ("II-4\n授权开发", ["通信和标识", "黑盒授权"], (255, 255, 255)),
        ("II-5\n版本管理", ["问题管理", "需求和版本\n管理", "规范管理"], (255, 255, 255)),
        ("II-10\n应用接口", ["应用接口协调", "车辆资源库", "动力传动", "底盘控制"], (255, 255, 255)),
    ]

    start_x = 45
    col_w = 190
    gap = 18
    y_top = 165
    for idx, (header, items, col_fill) in enumerate(columns):
        x = start_x + idx * (col_w + gap)
        draw_arrow(draw, (650, 125), (x + col_w // 2, y_top), width=2)
        draw_box(draw, (x, y_top, x + col_w, y_top + 70), header, font, fill=col_fill)
        y = y_top + 82
        for item in items:
            item_fill = blue if item in {"软件架构", "基础软件"} else (255, 255, 255)
            draw_box(draw, (x + 18, y, x + col_w - 18, y + 56), item, small, fill=item_fill, width=1)
            draw_arrow(draw, (x + col_w // 2, y - 12), (x + col_w // 2, y), width=1)
            y += 68

    note = "灰色/浅蓝区域表示本题项目关注的软件架构和基础软件部分。"
    draw.text((45, 725), note, font=small, fill=(80, 80, 80))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def make_fig_32(path):
    img = PILImage.new("RGB", (1100, 820), "white")
    draw = ImageDraw.Draw(img)
    title = load_font(28)
    font = load_font(22)
    small = load_font(18)
    green = (226, 245, 232)
    yellow = (255, 247, 214)
    blue = (226, 240, 255)

    draw.text((330, 25), "图 3-2  李工设计的流程", font=title, fill=(20, 20, 20))
    draw.text((60, 80), "输入：需求 & 车辆信息", font=font, fill=(20, 20, 20))

    boxes = {
        "swc": (70, 145, 270, 220),
        "sys": (450, 145, 650, 220),
        "ecu": (790, 145, 1010, 220),
        "step2": (405, 285, 700, 365),
        "step3": (435, 430, 670, 500),
        "step4": (405, 565, 700, 650),
        "out1": (70, 570, 270, 645),
        "out2": (780, 675, 1025, 750),
    }
    draw_box(draw, boxes["swc"], "IA\n软件组件\n描述", font, fill=green)
    draw_box(draw, boxes["sys"], "IC\n系统描述", font, fill=green)
    draw_box(draw, boxes["ecu"], "IB\nECU\n资源描述", font, fill=green)
    draw_box(draw, boxes["step2"], "2\n配置系统并\n生成 ECU\n描述的信息", font, fill=yellow)
    draw_box(draw, boxes["step3"], "3\n配置每个\nECU", font, fill=yellow)
    draw_box(draw, boxes["step4"], "4\n为每个 ECU\n生成可执行\n软件组件", font, fill=yellow)
    draw_box(draw, boxes["out1"], "软件组件", font, fill=blue)
    draw_box(draw, boxes["out2"], "各 ECU 的\n可执行软件", font, fill=blue)

    for key in ["swc", "sys", "ecu"]:
        b = boxes[key]
        draw_arrow(draw, ((b[0] + b[2]) // 2, b[3]), (552, boxes["step2"][1]), width=3)
    draw_arrow(draw, (552, boxes["step2"][3]), (552, boxes["step3"][1]), width=3)
    draw_arrow(draw, (552, boxes["step3"][3]), (552, boxes["step4"][1]), width=3)
    draw_arrow(draw, (boxes["swc"][0] + 100, boxes["swc"][3]), (boxes["out1"][0] + 100, boxes["out1"][1]), width=2)
    draw_arrow(draw, (boxes["out1"][2], boxes["out1"][1] + 35), (boxes["step4"][0], boxes["step4"][1] + 40), width=2)
    draw_arrow(draw, (boxes["step4"][2], boxes["step4"][1] + 40), (boxes["out2"][0], boxes["out2"][1] + 35), width=2)

    # Iteration hints.
    draw.line((1025, 185, 1060, 185, 1060, 600, 700, 600), fill=(120, 120, 120), width=2)
    draw_arrow(draw, (700, 600), (700, 600), fill=(120, 120, 120), width=2)
    draw.text((715, 395), "迭代修正和演化", font=small, fill=(80, 80, 80))
    draw.text((60, 735), "要点：软件组件描述、系统描述、ECU 资源描述可并发形成，并在配置过程中多轮迭代。", font=small, fill=(40, 40, 40))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def make_fig_33(path):
    img = PILImage.new("RGB", (1100, 820), "white")
    draw = ImageDraw.Draw(img)
    title = load_font(28)
    font = load_font(22)
    small = load_font(18)
    yellow = (255, 247, 214)
    red = (255, 232, 232)
    blue = (226, 240, 255)

    draw.text((330, 25), "图 3-3  王工设计的流程", font=title, fill=(20, 20, 20))
    draw.text((70, 80), "输入：需求 & 车辆信息", font=font, fill=(20, 20, 20))

    seq = [
        ("1\n系统描述", (410, 140, 690, 210)),
        ("2\n配置系统并\n生成 ECU 描述\n的信息", (410, 250, 690, 340)),
        ("3\n配置每个\nECU", (410, 385, 690, 455)),
        ("4\n软件组件", (410, 500, 690, 570)),
        ("5\n为每个 ECU\n生成可执行\n软件组件", (410, 615, 690, 710)),
    ]
    for text, box in seq:
        draw_box(draw, box, text, font, fill=yellow)
    for (_, b1), (_, b2) in zip(seq, seq[1:]):
        draw_arrow(draw, ((b1[0] + b1[2]) // 2, b1[3]), ((b2[0] + b2[2]) // 2, b2[1]), width=3)

    draw_box(draw, (80, 585, 300, 665), "6B\nECU 资源\n描述", font, fill=red)
    draw_box(draw, (760, 585, 1030, 675), "6A\n每个 ECU 的\n可执行软件组件", font, fill=blue)
    draw_arrow(draw, (300, 625), (410, 665), width=2)
    draw_arrow(draw, (690, 665), (760, 630), width=2)

    draw.line((1030, 630, 1060, 630, 1060, 180, 690, 180), fill=(120, 120, 120), width=2)
    draw.text((725, 360), "迭代修正和演化", font=small, fill=(80, 80, 80))
    draw.text((70, 735), "问题：流程偏串行，软件组件和 ECU 资源描述位置靠后，难以体现 AUTOSAR 的并发迭代。", font=small, fill=(40, 40, 40))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def make_fig_34(path):
    img = PILImage.new("RGB", (930, 760), "white")
    draw = ImageDraw.Draw(img)
    title = load_font(28)
    font = load_font(21)
    small = load_font(16)
    blue = (226, 240, 255)
    green = (226, 245, 232)
    yellow = (255, 247, 214)
    red = (255, 232, 232)

    draw.text((215, 25), "图 3-4  AUTOSAR 定义的操作系统结构", font=title, fill=(20, 20, 20))
    draw.rectangle((45, 80, 885, 690), outline=(40, 40, 40), width=3)

    # Top resource management.
    draw.text((65, 105), "资源管理", font=font, fill=(20, 20, 20))
    draw_box(draw, (640, 100, 835, 155), "资源控制块", font, fill=blue)

    # Task/process management.
    draw.text((65, 205), "进程管理和调度", font=font, fill=(20, 20, 20))
    draw_box(draw, (300, 205, 480, 260), "进程切换", font, fill=green)
    draw_box(draw, (635, 205, 835, 260), "任务控制块", font, fill=green)

    # Alarm management.
    draw.text((65, 325), "警报管理", font=font, fill=(20, 20, 20))
    draw_box(draw, (270, 325, 410, 380), "警报", font, fill=yellow)
    draw_box(draw, (465, 325, 605, 380), "活动", font, fill=yellow)

    # Counter.
    draw.text((65, 465), "计数器", font=font, fill=(20, 20, 20))
    draw_box(draw, (215, 465, 375, 520), "计数器", font, fill=yellow)

    # Events.
    draw_box(draw, (565, 465, 760, 520), "事件", font, fill=red)

    # Driver and interrupt layers.
    draw.rectangle((45, 570, 885, 620), outline=(40, 40, 40), width=2)
    draw_text_center(draw, (45, 570, 885, 620), "驱动", font)
    draw.rectangle((45, 620, 885, 690), outline=(40, 40, 40), width=2)
    draw_text_center(draw, (45, 620, 885, 690), "中断服务程序\n中断管理", font)

    # Internal structural arrows.
    draw_arrow(draw, (737, 155), (737, 205), width=2)
    draw_arrow(draw, (480, 232), (635, 232), width=2)
    draw_arrow(draw, (340, 260), (340, 325), width=2)
    draw_arrow(draw, (535, 260), (535, 325), width=2)
    draw_arrow(draw, (295, 520), (295, 570), width=2)
    draw_arrow(draw, (660, 520), (660, 570), width=2)

    # Numbered answer arrows.
    draw_arrow(draw, (315, 322), (315, 268), fill=(170, 20, 20), width=4)
    draw.text((285, 275), "(1)", font=small, fill=(170, 20, 20))

    draw_arrow(draw, (625, 325), (700, 262), fill=(170, 20, 20), width=4)
    draw.text((630, 290), "(2)", font=small, fill=(170, 20, 20))

    draw_arrow(draw, (535, 385), (650, 462), fill=(170, 20, 20), width=4)
    draw.text((560, 420), "(3)", font=small, fill=(170, 20, 20))

    draw_arrow(draw, (742, 160), (742, 202), fill=(170, 20, 20), width=4)
    draw.text((760, 172), "(4)", font=small, fill=(170, 20, 20))

    draw_arrow(draw, (745, 262), (745, 462), fill=(170, 20, 20), width=4)
    draw.text((760, 360), "(5)", font=small, fill=(170, 20, 20))

    draw.text((65, 705), "说明：本图根据题目截图重绘，红色箭头对应问题 2 的 1-5 操作。", font=small, fill=(80, 80, 80))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def ensure_images():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    make_fig_31(FIG_31)
    make_fig_32(FIG_32)
    make_fig_33(FIG_33)
    make_fig_34(FIG_34)


def make_styles(font_name):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CnTitle", parent=styles["Title"], fontName=font_name, fontSize=20, leading=28, alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="CnH2", parent=styles["Heading2"], fontName=font_name, fontSize=14, leading=20, spaceBefore=9, spaceAfter=6, textColor=colors.HexColor("#1f2937")))
    styles.add(ParagraphStyle(name="CnH3", parent=styles["Heading3"], fontName=font_name, fontSize=11.5, leading=17, spaceBefore=6, spaceAfter=4, textColor=colors.HexColor("#374151")))
    styles.add(ParagraphStyle(name="CnBody", parent=styles["BodyText"], fontName=font_name, fontSize=9.8, leading=15, spaceAfter=5))
    styles.add(ParagraphStyle(name="CnBullet", parent=styles["BodyText"], fontName=font_name, fontSize=9.8, leading=15, leftIndent=12, firstLineIndent=-8, spaceAfter=3))
    styles.add(ParagraphStyle(name="CnCode", parent=styles["Code"], fontName=font_name, fontSize=8.8, leading=12, backColor=colors.HexColor("#f3f4f6"), borderColor=colors.HexColor("#e5e7eb"), borderWidth=0.5, borderPadding=5, spaceBefore=3, spaceAfter=6))
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
        title="AUTOSAR汽车电子基础软件架构-快速记忆",
        author="Codex",
    )
    md_text = MD_PATH.read_text(encoding="utf-8")
    doc.build(markdown_to_flowables(md_text, styles, doc.width))


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)
