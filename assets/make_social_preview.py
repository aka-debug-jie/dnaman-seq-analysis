"""Generate assets/social-preview.png (1280x640) for the GitHub repository page.

    python assets/make_social_preview.py

The image is drawn from scratch - no DNAMAN screenshot or other third-party
artwork is used. Upload the result under Settings -> Social preview, because
the GitHub API does not expose that setting.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 640
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "social-preview.png")

BG_TOP = (13, 17, 23)
BG_BOTTOM = (9, 34, 43)
ACCENT = (56, 189, 248)
ACCENT_2 = (52, 211, 153)
TEXT = (240, 246, 252)
MUTED = (139, 148, 158)

CJK_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/msyh.ttc",
]
LATIN_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
]


def _first_existing(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    raise SystemExit("no usable font found, tried:\n  " + "\n  ".join(paths))


def font(size, cjk=False, bold=False):
    if cjk:
        path = _first_existing(
            [p for p in CJK_CANDIDATES if bold or "Bold" not in p] or CJK_CANDIDATES
        )
    else:
        path = _first_existing(
            [p for p in LATIN_CANDIDATES if bold or "Bold" not in p] or LATIN_CANDIDATES
        )
    return ImageFont.truetype(path, size)


def gradient(size):
    img = Image.new("RGB", size, BG_TOP)
    top = Image.new("RGB", (1, size[1]))
    d = ImageDraw.Draw(top)
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        d.point((0, y), tuple(int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM)))
    return img.paste(top.resize(size), (0, 0)) or img


def helix(draw, x0, y0, height, turns, radius, color, rungs=26):
    """A stylised DNA double helix drawn as two sine waves plus base rungs."""
    steps = 480
    for phase, c in ((0.0, color), (math.pi, tuple(v // 2 for v in color))):
        pts = []
        for i in range(steps + 1):
            t = i / steps
            y = y0 + t * height
            x = x0 + radius * math.sin(2 * math.pi * turns * t + phase)
            pts.append((x, y))
        draw.line(pts, fill=c, width=5, joint="curve")
    for k in range(rungs + 1):
        t = k / rungs
        y = y0 + t * height
        a = x0 + radius * math.sin(2 * math.pi * turns * t)
        b = x0 + radius * math.sin(2 * math.pi * turns * t + math.pi)
        draw.line([(a, y), (b, y)], fill=tuple(v // 3 for v in color), width=2)


def main():
    img = gradient((W, H))
    draw = ImageDraw.Draw(img)

    helix(draw, W - 210, -40, H + 80, turns=3.2, radius=88, color=ACCENT)

    draw.rectangle([0, 0, 10, H], fill=ACCENT)

    x = 84
    draw.text((x, 96), "dnaman-seq-analysis", font=font(58, bold=True), fill=TEXT)

    draw.text((x, 178), "用 Python 和 AI 代理驱动 DNAMAN 4.0",
              font=font(34, cjk=True, bold=True), fill=ACCENT_2)
    draw.text((x, 228), "Drive the legacy Windows GUI from Python & AI agents",
              font=font(22), fill=MUTED)

    draw.line([(x, 288), (x + 620, 288)], fill=(48, 54, 61), width=2)

    chips = ["酶切分析", "引物设计", "ORF", "序列组装", "双序列比对", "蛋白工具"]
    cx, cy, f = x, 320, font(21, cjk=True)
    for chip in chips:
        w = draw.textlength(chip, font=f)
        draw.rounded_rectangle([cx, cy, cx + w + 32, cy + 46], radius=23,
                               outline=(48, 54, 61), width=2)
        draw.text((cx + 16, cy + 10), chip, font=f, fill=TEXT)
        cx += w + 44
        if cx > x + 600:
            cx, cy = x, cy + 60

    draw.text((x, H - 118), "DNAMAN-first, Python fallback:",
              font=font(21, cjk=False), fill=MUTED)
    draw.text((x, H - 86), "Biopython · primer3-py · pydna · MAFFT · BLAST+",
              font=font(21, bold=True), fill=TEXT)
    draw.text((x, H - 48), "windows-only  ·  python 3.9+  ·  MIT",
              font=font(19), fill=MUTED)

    img.save(OUT)
    print("wrote %s (%dx%d)" % (OUT, W, H))


if __name__ == "__main__":
    main()
