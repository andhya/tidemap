#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy==2.5.4", "pillow==13.0.0", "pytmd==3.1.0"]
# ///
"""Hourly job: keep site/api/map/HH00Z.png holding the next occurrence of each UTC hour."""

import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from render import render_png

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
INDEX = Path(__file__).parent / "index.html"
FIELDS = ROOT / "data" / "fields.npz"


def filename(when: datetime) -> str:
    return f"{when.hour:02d}00Z.png"


def targets(now: datetime) -> list[datetime]:
    """The current hour first, then the following 23."""
    hour = now.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return [hour + timedelta(hours=h) for h in range(24)]


def write_atomic(path: Path, data: bytes) -> None:
    temp = path.with_suffix(".tmp")
    temp.write_bytes(data)
    os.replace(temp, path)


def point_now(maps: Path, target: str) -> None:
    link = maps / "now.tmp"
    link.unlink(missing_ok=True)
    link.symlink_to(target)
    os.replace(link, maps / "now.png")


def run(render, now: datetime, site: Path = SITE) -> list[str]:
    """Render whatever is stale via render(when) -> bytes; returns the files written."""
    maps = site / "api" / "map"
    maps.mkdir(parents=True, exist_ok=True)
    manifest_path = maps / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    written = []
    wanted = targets(now)
    for i, when in enumerate(wanted):
        name = filename(when)
        if manifest.get(name) != when.isoformat() or not (maps / name).exists():
            write_atomic(maps / name, render(when))
            manifest[name] = when.isoformat()
            written.append(name)
        if i == 0:
            point_now(maps, name)
    write_atomic(manifest_path, json.dumps(manifest, indent=1, sort_keys=True).encode())
    return written


def main() -> None:
    SITE.mkdir(exist_ok=True)
    shutil.copyfile(INDEX, SITE / "index.html")
    model = None

    def render(when: datetime) -> bytes:
        nonlocal model
        if model is None:  # most runs need one frame, but never load for none
            from model import TideModel

            model = TideModel(FIELDS)
        return render_png(model.sea_index, model.heights_above_cd(when))

    written = run(render, datetime.now(timezone.utc))
    print(f"rendered {len(written)}: {' '.join(written)}", flush=True)


if __name__ == "__main__":
    main()
