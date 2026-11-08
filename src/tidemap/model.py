"""Tide prediction"""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyTMD.constituents

MJD_UNIX_EPOCH = 40587.0
CORRECTIONS = "GOT"


class TideModel:
    def __init__(self, path: Path):
        with np.load(path) as data:
            self.constituents = [str(c) for c in data["constituents"]]
            self.sea_index = data["sea_index"]
            self.real_mm = data["real_mm"]  # constituents x sea pixels
            self.imag_mm = data["imag_mm"]
            self.msl_above_cd = data["msl_above_cd"]
        with np.load(path.with_name("seabed.npz")) as data:
            self.depth_m = data["depth_m"]
            self.relief = data["relief"]

    def heights_above_cd(self, when: datetime) -> np.ndarray:
        """Height above chart datum, in metres, at every sea pixel."""
        mjd = when.astimezone(timezone.utc).timestamp() / 86400.0 + MJD_UNIX_EPOCH
        pu, pf, G = pyTMD.constituents.arguments(
            np.atleast_1d(mjd), self.constituents, corrections=CORRECTIONS
        )
        theta = np.radians(G) + pu
        c, s = (pf * np.cos(theta))[0], (-pf * np.sin(theta))[0]
        tide = np.zeros(self.sea_index.size, dtype=np.float32)
        for i in range(len(self.constituents)):
            tide += float(c[i]) * self.real_mm[i].astype(np.float32)
            tide += float(s[i]) * self.imag_mm[i].astype(np.float32)
        return tide / 1000.0 + self.msl_above_cd
