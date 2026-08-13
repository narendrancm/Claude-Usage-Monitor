"""
Dynamic System Tray Icon Generator.
Uses Pillow to create high-craft monochrome tray icons with semantic status indicators.
"""
from PIL import Image, ImageDraw
from typing import Dict, Tuple
from models.usage import StatusLevel

_ICON_CACHE: Dict[Tuple[StatusLevel, int], Image.Image] = {}

def get_status_color(status: StatusLevel) -> Tuple[int, int, int, int]:
    if status == StatusLevel.SAFE:
        return (16, 185, 129, 255)     # #10b981
    elif status == StatusLevel.WARNING:
        return (245, 158, 11, 255)     # #f59e0b
    elif status == StatusLevel.CRITICAL:
        return (239, 68, 68, 255)      # #ef4444
    else:
        return (115, 115, 115, 255)    # #737373 neutral grey

def create_tray_icon(status: StatusLevel = StatusLevel.SAFE, size: int = 64) -> Image.Image:
    """Generates a crisp monochrome tray icon with a subtle status indicator."""
    cache_key = (status, size)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    # Create RGBA canvas
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = size // 8
    width = size - 2 * margin

    # Dark monochrome circle background
    draw.ellipse(
        [margin, margin, margin + width, margin + width],
        fill=(20, 20, 20, 255),
        outline=(50, 50, 50, 255),
        width=max(1, size // 32)
    )

    # Inner typographic 'C' symbol in white
    cx, cy = size // 2, size // 2
    r_outer = size // 4
    r_inner = size // 7

    # Draw letter 'C' arc
    draw.arc(
        [cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
        start=45,
        end=315,
        fill=(245, 245, 245, 255),
        width=max(2, size // 12)
    )

    # Status accent dot on bottom right
    dot_radius = size // 7
    dot_cx = size - margin - dot_radius
    dot_cy = size - margin - dot_radius
    dot_color = get_status_color(status)

    # White border around dot for contrast
    draw.ellipse(
        [dot_cx - dot_radius - 2, dot_cy - dot_radius - 2, dot_cx + dot_radius + 2, dot_cy + dot_radius + 2],
        fill=(10, 10, 10, 255)
    )
    draw.ellipse(
        [dot_cx - dot_radius, dot_cy - dot_radius, dot_cx + dot_radius, dot_cy + dot_radius],
        fill=dot_color
    )

    _ICON_CACHE[cache_key] = img
    return img
