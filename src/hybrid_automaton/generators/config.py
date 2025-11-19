from enum import Enum
from dataclasses import dataclass


class OutputFormat(Enum):
    SVG = "svg"
    PNG = "png"


class Theme(Enum):
    DEFAULT = "default"
    NEUTRAL = "neutral"
    DARK = "dark"
    FOREST = "forest"
    BASE = "base"


class Background(Enum):
    TRANSPARENT = "transparent"
    WHITE = "white"
    BLACK = "black"


@dataclass
class DiagramConfig:
    theme: Theme = Theme.FOREST
    background: Background = Background.WHITE
    scale: int = 2
    output_format: OutputFormat = OutputFormat.SVG