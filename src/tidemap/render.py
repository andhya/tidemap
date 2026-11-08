"""map rendered for eink display"""

from io import BytesIO

import numpy as np
from PIL import Image

WIDTH = 1200
HEIGHT = 1600
LAND = (255, 255, 255)
# (metres above chart datum, RGB): flat below the first stop and above the last.
RAMP = (
    (1.0, (222, 196, 142)),  # sand
    (4.0, (0, 0, 255)),  # pure blue
    (10.0, (0, 0, 64)),  # deep navy
)


def colours(heights: np.ndarray) -> np.ndarray:
    stops = [s[0] for s in RAMP]
    return np.stack(
        [np.interp(heights, stops, [s[1][i] for s in RAMP]) for i in range(3)], axis=-1
    ).round().astype(np.uint8)


def render_png(sea_index: np.ndarray, heights: np.ndarray) -> bytes:
    rgb = np.full((HEIGHT * WIDTH, 3), LAND, dtype=np.uint8)
    rgb[sea_index] = colours(heights)
    image = Image.fromarray(rgb.reshape(HEIGHT, WIDTH, 3), "RGB")
    out = BytesIO()
    image.save(out, "PNG", compress_level=6)
    return out.getvalue()
