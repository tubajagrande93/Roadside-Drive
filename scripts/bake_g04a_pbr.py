"""Bake original, repeatable Roadside Drive starter PBR textures (NOT scanned photos).

Requires NumPy and Pillow already in Roadside Drive's uv environment.
Output: PNG albedo, normal and roughness for asphalt, paving and concrete.
No network, no copyrighted source images, no external texture library.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

SEED = 42717


def smooth(t):
    return t * t * (3 - 2 * t)


def periodic_noise(size, cells, rng):
    # Bilinear periodic samples, so the left/right and top/bottom tile edges match.
    nodes = rng.normal(0, 1, (cells, cells)).astype(np.float32)
    pos = np.arange(size, dtype=np.float32) * (cells / size)
    index = np.floor(pos).astype(np.int32)
    f = smooth(pos - index)
    a, b = index % cells, (index + 1) % cells
    n00 = nodes[a[:, None], a[None, :]]
    n10 = nodes[b[:, None], a[None, :]]
    n01 = nodes[a[:, None], b[None, :]]
    n11 = nodes[b[:, None], b[None, :]]
    wx = f[:, None]
    wy = f[None, :]
    return (
        n00 * (1 - wx) * (1 - wy)
        + n10 * wx * (1 - wy)
        + n01 * (1 - wx) * wy
        + n11 * wx * wy
    )


def maps(size, kind):
    rng = np.random.default_rng(SEED + {"asphalt": 1, "paving": 2, "concrete": 3}[kind])
    noise = (
        0.42 * periodic_noise(size, 8, rng)
        + 0.32 * periodic_noise(size, 32, rng)
        + 0.17 * periodic_noise(size, 128, rng)
        + 0.09 * periodic_noise(size, 256, rng)
    )
    grain = periodic_noise(size, min(512, size // 2), rng)
    h = 0.78 * noise + 0.22 * grain
    h = h / (max(np.std(h), 1e-5) * 3.8)
    x = np.arange(size, dtype=np.float32)[:, None]
    y = np.arange(size, dtype=np.float32)[None, :]
    if kind == "asphalt":
        # Dark neutral asphalt flecked with tiny original stones.
        fleck = (grain > 0.75).astype(np.float32)
        base = np.array([82, 86, 88], dtype=np.float32)
        rgb = base[None, None, :] + h[:, :, None] * 27 + fleck[:, :, None] * 12
        rough = np.clip(207 + h * 10, 163, 236)
        strength = 3.0
    elif kind == "paving":
        # Original orthogonal paver tiling; pattern repeats at every image edge.
        # Slight alternating color by paver index and fine mortar grooves.
        nx, ny = 8, 12
        ux = (x / (size / nx)) % 1
        uy = (y / (size / ny)) % 1
        joint = np.minimum.reduce(np.broadcast_arrays(ux, 1 - ux, uy, 1 - uy))
        mortar = (joint < 0.025).astype(np.float32)
        blocks = ((np.floor(x / (size / nx)) + np.floor(y / (size / ny)) * 3) % 5) / 5
        blocks = np.broadcast_to(blocks, (size, size))
        base = np.array([151, 150, 143], dtype=np.float32)
        rgb = (
            base + h[:, :, None] * 22 + blocks[:, :, None] * 8 - mortar[:, :, None] * 36
        )
        rough = np.clip(194 + h * 9 + mortar * 12, 155, 237)
        h = h - mortar * 0.6
        strength = 2.0
    else:
        # Neutral light-gray curb block / concrete. Use top-down only if needed.
        base = np.array([174, 173, 166], dtype=np.float32)
        rgb = base + h[:, :, None] * 16
        rough = np.clip(185 + h * 8, 156, 225)
        strength = 1.2
    # Seamless normal from wrap-derivative (geometry remains flat).
    gx = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * strength
    gy = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * strength
    normal = np.stack([-gx, -gy, np.ones_like(gx) * 3.7], axis=2)
    normal /= np.maximum(np.linalg.norm(normal, axis=2, keepdims=True), 1e-9)
    normal = (normal * 0.5 + 0.5) * 255
    return np.uint8(np.clip(rgb, 0, 255)), np.uint8(normal), np.uint8(rough)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bake(out, size=1024):
    if size < 256 or size > 2048 or (size & (size - 1)):
        raise ValueError("size must be power of two between 256 and 2048")
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    for kind in ["asphalt", "paving", "concrete"]:
        color, normal, rough = maps(size, kind)
        for suffix, arr, mode in [
            ("albedo", color, "RGB"),
            ("normal", normal, "RGB"),
            ("roughness", rough, "L"),
        ]:
            name = f"RD_G04A_{kind}_{suffix}_{size}.png"
            p = out / name
            Image.fromarray(arr, mode=mode).save(p, optimize=True)
            files[name] = {
                "sha256": digest(p),
                "bytes": p.stat().st_size,
                "mode": mode,
                "size": [size, size],
                "color_space": "sRGB" if suffix == "albedo" else "linear",
                "texture_kind": kind,
                "channel": suffix,
            }
    m = {
        "schema": "RD-G04A-PBR-1",
        "seed": SEED,
        "origin": "ORIGINAL_SYNTHETIC_GENERATOR",
        "license": "PROJECT_ORIGINAL",
        "quality": "PROCEDURAL_STARTER_NOT_PHOTOREAL_SCAN",
        "assets": files,
    }
    (out / "texture_manifest.json").write_text(
        json.dumps(m, indent=2, sort_keys=True) + "\n", encoding="utf8"
    )
    return m


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--size", type=int, default=1024)
    a = p.parse_args()
    m = bake(a.out, a.size)
    print(
        json.dumps(
            {"assets": len(m["assets"]), "output": str(a.out.resolve())}, indent=2
        )
    )


if __name__ == "__main__":
    main()
