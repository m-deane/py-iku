"""
Recipe type icons for Dataiku flow visualization.
"""

from typing import Dict


class RecipeIcons:
    """Icons for different Dataiku recipe types."""

    # Unicode icons for each recipe type
    UNICODE: Dict[str, str] = {
        "prepare": "\u2699",      # ⚙ Gear
        "join": "\u22c8",         # ⋈ Bowtie (join symbol)
        "stack": "\u2630",        # ☰ Trigram (stacked lines)
        "grouping": "\u03a3",     # Σ Sigma (sum)
        "window": "\u25a6",       # ▦ Square with grid
        "split": "\u2442",        # ⑂ Fork
        "sort": "\u21c5",         # ⇅ Up down arrows
        "distinct": "\u25ce",     # ◎ Bullseye
        "filter": "\u25bc",       # ▼ Down triangle (funnel)
        "python": "\u03bb",       # λ Lambda (code)
        "sync": "\u21c4",         # ⇄ Left right arrows
        "sample": "\u25d4",       # ◔ Circle with quarter
        "pivot": "\u229e",        # ⊞ Squared plus
        "top_n": "\u2191",        # ↑ Up arrow
        "default": "\u25a0",      # ■ Square
    }

    # Text labels for recipe types
    LABELS: Dict[str, str] = {
        "prepare": "Prepare",
        "join": "Join",
        "stack": "Stack",
        "grouping": "Grouping",
        "window": "Window",
        "split": "Split",
        "sort": "Sort",
        "distinct": "Distinct",
        "filter": "Filter",
        "python": "Python",
        "sync": "Sync",
        "sample": "Sample",
        "pivot": "Pivot",
        "top_n": "Top N",
        "default": "Recipe",
    }

    # SVG path icons (for high-quality rendering)
    SVG_PATHS: Dict[str, str] = {
        "prepare": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z",
        "join": "M12 2L4 7v10l8 5 8-5V7l-8-5zm0 2.5l6 3.75v7.5L12 19.5l-6-3.75v-7.5L12 4.5z",
        "grouping": "M4 4h6v6H4V4zm10 0h6v6h-6V4zM4 14h6v6H4v-6zm10 0h6v6h-6v-6z",
        "split": "M12 2v8h8M12 2v8H4M12 22v-8h8M12 22v-8H4",
        "default": "M4 4h16v16H4V4z",
    }

    # ASCII representations for terminal output
    ASCII: Dict[str, str] = {
        "prepare": "[*]",
        "join": "[><]",
        "stack": "[=]",
        "grouping": "[E]",
        "window": "[#]",
        "split": "[Y]",
        "sort": "[|]",
        "distinct": "[O]",
        "filter": "[V]",
        "python": "[Py]",
        "sync": "[<>]",
        "sample": "[%]",
        "pivot": "[+]",
        "top_n": "[^]",
        "default": "[?]",
    }

    @classmethod
    def get_unicode(cls, recipe_type: str) -> str:
        """Get Unicode icon for recipe type."""
        recipe_type = recipe_type.lower().replace(" ", "_")
        return cls.UNICODE.get(recipe_type, cls.UNICODE["default"])

    @classmethod
    def get_label(cls, recipe_type: str) -> str:
        """Get text label for recipe type."""
        recipe_type = recipe_type.lower().replace(" ", "_")
        return cls.LABELS.get(recipe_type, cls.LABELS["default"])

    @classmethod
    def get_ascii(cls, recipe_type: str) -> str:
        """Get ASCII representation for recipe type."""
        recipe_type = recipe_type.lower().replace(" ", "_")
        return cls.ASCII.get(recipe_type, cls.ASCII["default"])

    @classmethod
    def get_svg_path(cls, recipe_type: str) -> str:
        """Get SVG path for recipe type."""
        recipe_type = recipe_type.lower().replace(" ", "_")
        return cls.SVG_PATHS.get(recipe_type, cls.SVG_PATHS["default"])
