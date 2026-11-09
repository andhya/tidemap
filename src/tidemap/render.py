"""map rendered for eink display"""

from datetime import datetime
from io import BytesIO
from math import cos, radians, sin
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1200
HEIGHT = 1600
LAND = (255, 255, 255)
# Tide, in metres above chart datum: the seabed shows below TIDE_LOW, then blue, then navy.
TIDE_LOW = 1.0
TIDE_BLUE = 4.0
TIDE_NAVY = 10.0
BLUE = np.array((0.0, 0.0, 255.0), dtype=np.float32)
NAVY = np.array((0.0, 0.0, 64.0), dtype=np.float32)
# (metres deep, RGB): linear to the last stop, then a log fade to DEEP_RGB at DEEPEST.
SEABED = (
    (10.0, (222, 196, 142)),  # sand
    (100.0, (204, 204, 204)),  # 20% grey
    (200.0, (178, 178, 178)),  # 30% grey
)
DEEPEST = 3738.0
DEEP_RGB = np.array((128.0, 128.0, 128.0), dtype=np.float32)  # 50% grey
CLOCK_ZONE = ZoneInfo("Europe/London")
CLOCK_FACE = (204, 204, 204)  # 20% grey
CLOCK_INK = (0, 0, 0)
CLOCK_DIAMETER = WIDTH // 16
CLOCK_MARGIN = 40 + CLOCK_DIAMETER // 2  # from the right and bottom edges
CLOCK_FONT_PX = 22
CLOCK_SCALE = 4  # supersampling for smooth edges
# Helvetica, or the metric-compatible stand-ins
FONTS = ("Helvetica.ttf", "Arimo-Regular.ttf", "LiberationSans-Regular.ttf", "NimbusSans-Regular.otf", "DejaVuSans.ttf")
RELIEF_SCALE = 360.0  # stored units per unit of relief; positive is deeper than nearby


def seabed(depth_m: np.ndarray) -> np.ndarray:
    depth_m = depth_m.astype(np.float32)
    stops = [s[0] for s in SEABED]
    rgb = np.stack(
        [np.interp(depth_m, stops, [s[1][i] for s in SEABED]).astype(np.float32) for i in range(3)], axis=-1
    )
    fade = np.log(np.clip(depth_m, stops[-1], DEEPEST) / stops[-1]) / np.log(DEEPEST / stops[-1])
    return rgb + (DEEP_RGB - rgb) * fade[:, None]


def colours(heights: np.ndarray, depth_m: np.ndarray, relief: np.ndarray) -> np.ndarray:
    blue = np.clip((heights - TIDE_LOW) / (TIDE_BLUE - TIDE_LOW), 0, 1)[:, None]
    navy = np.clip((heights - TIDE_BLUE) / (TIDE_NAVY - TIDE_BLUE), 0, 1)[:, None]
    rgb = (seabed(depth_m) * (1 - blue) + BLUE * blue) * (1 - navy) + NAVY * navy
    shade = relief[:, None].astype(np.float32) / RELIEF_SCALE * blue  # channels darker, banks lighter, tide only
    rgb *= 1 - shade.clip(0)
    rgb += (255 - rgb) * -shade.clip(max=0)
    return rgb.round().astype(np.uint8)


def font(px: int) -> ImageFont.FreeTypeFont:
    for name in FONTS:
        try:
            return ImageFont.truetype(name, px)
        except OSError:
            continue
    return ImageFont.load_default(px)


def draw_clock(image: Image.Image, when: datetime) -> None:
    """Bottom right: a grey face with an hour hand, and the day and date below, in UK local time."""
    local = when.astimezone(CLOCK_ZONE)
    label = f"{local:%a} {local.day}".upper()
    text_font = font(CLOCK_FONT_PX)
    text_w = text_font.getlength(label)
    text_h = CLOCK_FONT_PX
    gap = CLOCK_FONT_PX // 2

    k = CLOCK_SCALE
    r = CLOCK_DIAMETER / 2
    box_w = int(max(CLOCK_DIAMETER, text_w)) + 4
    box_h = int(CLOCK_DIAMETER + gap + text_h) + 8
    face = Image.new("L", (box_w * k, box_h * k), 0)  # coverage masks
    ink = Image.new("L", face.size, 0)
    cx, cy = box_w * k / 2, (2 + r) * k
    ImageDraw.Draw(face).ellipse((cx - r * k, cy - r * k, cx + r * k, cy + r * k), fill=255)
    pen = ImageDraw.Draw(ink)

    def pt(angle: float, along: float, across: float = 0.0) -> tuple[float, float]:
        """angle clockwise from 12; along the hand, across to its right, in units of r."""
        a = radians(angle)
        x = along * sin(a) + across * cos(a)
        y = -along * cos(a) + across * sin(a)
        return cx + x * r * k, cy + y * r * k

    for angle in (0, 90, 180, 270):  # thin radial marks just inside the rim
        pen.polygon([pt(angle, 0.74, -0.017), pt(angle, 0.74, 0.017), pt(angle, 0.94, 0.017), pt(angle, 0.94, -0.017)], fill=255)
    angle = (local.hour % 12 + local.minute / 60) * 30
    pen.polygon([pt(angle, 0.78), pt(angle, 0, 0.07), pt(angle, -0.25), pt(angle, 0, -0.07)], fill=255)

    size = (box_w, box_h)
    face = face.resize(size, Image.LANCZOS)
    ink = ink.resize(size, Image.LANCZOS)
    left = WIDTH - CLOCK_MARGIN - box_w
    top = round(HEIGHT - (CLOCK_MARGIN + box_w / 2) - 2 - r)  # face centre as far from the bottom as from the right
    image.paste(Image.new("RGB", size, CLOCK_FACE), (left, top), face)
    image.paste(Image.new("RGB", size, CLOCK_INK), (left, top), ink)
    ImageDraw.Draw(image).text(
        (left + box_w / 2, top + 2 + CLOCK_DIAMETER + gap), label, font=text_font, fill=CLOCK_INK, anchor="mt"
    )


def render_png(
    sea_index: np.ndarray, heights: np.ndarray, depth_m: np.ndarray, relief: np.ndarray, when: datetime
) -> bytes:
    rgb = np.full((HEIGHT * WIDTH, 3), LAND, dtype=np.uint8)
    rgb[sea_index] = colours(heights, depth_m, relief)
    image = Image.fromarray(rgb.reshape(HEIGHT, WIDTH, 3), "RGB")
    draw_clock(image, when)
    out = BytesIO()
    image.save(out, "PNG", compress_level=6)
    return out.getvalue()
