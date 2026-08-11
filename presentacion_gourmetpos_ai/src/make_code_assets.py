from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1] / "scratch" / "assets"
OUT.mkdir(parents=True, exist_ok=True)


SNIPPETS = [
    {
        "path": ROOT / "backend" / "main.py",
        "name": "code_main.png",
        "title": "backend/main.py",
        "ranges": [(78, 88), (148, 164)],
    },
    {
        "path": ROOT / "backend" / "services" / "whatsapp_service.py",
        "name": "code_whatsapp_service.png",
        "title": "backend/services/whatsapp_service.py",
        "ranges": [(347, 370), (754, 767)],
    },
    {
        "path": ROOT / "whatsapp_bot" / "prompts.py",
        "name": "code_prompts.png",
        "title": "whatsapp_bot/prompts.py",
        "ranges": [(336, 360)],
    },
    {
        "path": ROOT / "frontend" / "assets" / "js" / "api.js",
        "name": "code_api.png",
        "title": "frontend/assets/js/api.js",
        "ranges": [(3, 40), (86, 100)],
    },
]


def load_font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/CascadiaMono.ttf",
        "C:/Windows/Fonts/lucon.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT = load_font(24)
FONT_BOLD = load_font(28, bold=True)
FONT_SMALL = load_font(19)


def collect_lines(path: Path, ranges):
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
    result = []
    for start, end in ranges:
        for line_no in range(start, min(end, len(raw)) + 1):
            text = raw[line_no - 1].replace("\t", "    ")
            if len(text) > 86:
                text = text[:83] + "..."
            result.append((line_no, text))
        result.append((None, ""))
    return result[:-1]


def syntax_color(text: str):
    stripped = text.strip()
    if stripped.startswith("#"):
        return "#7DD3FC"
    if stripped.startswith(("class ", "def ", "async def ", "@")):
        return "#FBBF24"
    if any(stripped.startswith(k) for k in ("from ", "import ", "return ", "if ", "for ", "try:", "except")):
        return "#A7F3D0"
    if "=" in stripped or ":" in stripped:
        return "#E5E7EB"
    return "#CBD5E1"


def draw_code_card(spec):
    width, height = 1280, 760
    img = Image.new("RGB", (width, height), "#0B1018")
    draw = ImageDraw.Draw(img)

    # Header
    draw.rounded_rectangle((0, 0, width, height), radius=26, fill="#0B1018", outline="#263246", width=2)
    draw.rounded_rectangle((0, 0, width, 86), radius=26, fill="#121A27")
    draw.rectangle((0, 58, width, 86), fill="#121A27")
    for i, color in enumerate(["#FF5F56", "#FFBD2E", "#27C93F"]):
        draw.ellipse((34 + i * 36, 28, 54 + i * 36, 48), fill=color)
    draw.text((168, 25), spec["title"], font=FONT_BOLD, fill="#F8FAFC")

    y = 118
    lines = collect_lines(spec["path"], spec["ranges"])
    for line_no, text in lines:
        if y > height - 42:
            break
        if line_no is None:
            y += 16
            continue
        draw.text((42, y), f"{line_no:>3}", font=FONT_SMALL, fill="#64748B")
        draw.text((104, y), text, font=FONT, fill=syntax_color(text))
        y += 32

    img.save(OUT / spec["name"])
    print(OUT / spec["name"])


for snippet in SNIPPETS:
    draw_code_card(snippet)
