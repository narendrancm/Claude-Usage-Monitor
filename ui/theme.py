"""
Monochrome Editorial Design System Tokens.
"""
from dataclasses import dataclass

@dataclass
class ThemeColors:
    bg_primary: str
    bg_surface: str
    bg_card: str
    border: str
    text_primary: str
    text_secondary: str
    text_muted: str
    accent_safe: str
    accent_warning: str
    accent_critical: str
    accent_grey: str

DARK_THEME = ThemeColors(
    bg_primary="#0a0a0a",
    bg_surface="#141414",
    bg_card="#1c1c1c",
    border="#282828",
    text_primary="#f5f5f5",
    text_secondary="#a0a0a0",
    text_muted="#666666",
    accent_safe="#10b981",
    accent_warning="#f59e0b",
    accent_critical="#ef4444",
    accent_grey="#737373"
)

LIGHT_THEME = ThemeColors(
    bg_primary="#f7f7f7",
    bg_surface="#ffffff",
    bg_card="#f0f0f0",
    border="#e0e0e0",
    text_primary="#0a0a0a",
    text_secondary="#555555",
    text_muted="#888888",
    accent_safe="#059669",
    accent_warning="#d97706",
    accent_critical="#dc2626",
    accent_grey="#9ca3af"
)
