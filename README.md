# tidemap

Hourly tide-height maps of UK waters. Needs Linux, systemd and [uv](https://docs.astral.sh/uv/).

## Deploy

```sh
git clone https://github.com/andhya/tidemap ~/tidemap && ~/tidemap/deploy/install.sh
```

## UI

`http://HOST:8400/`

## API

1200 x 1600 PNGs, times in UTC:

- `/api/map/now.png`: current hour
- `/api/map/HH00Z.png`: next occurrence of that hour, `0000Z` to `2300Z`
- `/api/map/manifest.json`: valid time of each file

Not for navigation. Data: EOT20, TICON-3 and EMODnet Bathymetry (CC-BY 4.0), GSHHG (LGPL).
