"""map rendered for eink display"""

from io import BytesIO

import numpy as np
from PIL import Image

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


def render_png(sea_index: np.ndarray, heights: np.ndarray, depth_m: np.ndarray, relief: np.ndarray) -> bytes:
    rgb = np.full((HEIGHT * WIDTH, 3), LAND, dtype=np.uint8)
    rgb[sea_index] = colours(heights, depth_m, relief)
    image = Image.fromarray(rgb.reshape(HEIGHT, WIDTH, 3), "RGB")
    out = BytesIO()
    image.save(out, "PNG", compress_level=6)
    return out.getvalue()
