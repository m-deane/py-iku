"""
Recipe type icons for Dataiku flow visualization.

The icon paths follow Dataiku DSS visual conventions: each recipe type maps to
a colored circle node with an icon at its center. Paths use a 24x24 viewBox so
they composite cleanly into circles of any size.

Path data is hand-rolled with shapes inspired by FontAwesome-Free 6.4 and
Material Symbols Outlined. Where DSS uses a custom mark with no clean public
analog (PREPARE's broom-and-dustpan, JOIN's bowtie ⋈), we draw an abstraction
that reads at a glance.
"""

from __future__ import annotations


class RecipeIcons:
    """Icons for different Dataiku recipe types.

    Lookup keys are normalized: lowercased, with spaces converted to
    underscores. Both DSS-canonical names (``fuzzyjoin``) and friendly aliases
    (``fuzzy_join``) resolve to the same icon.
    """

    # Unicode icons for each recipe type — broadly supported single glyphs that
    # render in any monospace terminal font.
    UNICODE: dict[str, str] = {
        # Visual recipes
        "prepare": "⚙",        # ⚙ Gear
        "join": "⋈",           # ⋈ Bowtie (join symbol)
        "fuzzyjoin": "≋",      # ≋ Triple tilde (fuzzy)
        "fuzzy_join": "≋",
        "geojoin": "⌖",        # ⌖ Position indicator
        "geo_join": "⌖",
        "stack": "☰",          # ☰ Trigram (stacked lines)
        "grouping": "Σ",       # Σ Sigma (sum)
        "window": "▦",         # ▦ Square with grid
        "split": "⑂",          # ⑂ Fork
        "sort": "⇅",           # ⇅ Up down arrows
        "distinct": "★",       # ★ Star (unique)
        "filter": "▼",         # ▼ Down triangle (funnel)
        "sync": "⇄",           # ⇄ Left right arrows
        "sample": "%",         # % Percent
        "sampling": "%",       # % Percent
        "pivot": "⊞",          # ⊞ Squared plus
        "top_n": "↑",          # ↑ Up arrow
        "topn": "↑",
        "download": "⤓",       # ⤓ Down to bar arrow
        "generate_features": "✨",  # ✨ Sparkles
        "generate_statistics": "σ",  # σ Std dev
        "push_to_editable": "✎",   # ✎ Pencil
        "list_folder_contents": "☰",  # ☰
        "dynamic_repeat": "↻",     # ↻ Clockwise
        "extract_failed_rows": "⚠",  # ⚠ Warning
        "upsert": "⇆",         # ⇆ Both arrows
        "list_access": "☰",    # ☰

        # Code recipes
        "python": "\U0001f40d",     # 🐍 Snake
        "r": "Ⓡ",              # Ⓡ Circled R
        "sql": "\U0001f5c4",        # 🗄 File cabinet
        "sql_script": "\U0001f5c4",
        "hive": "\U0001f41d",       # 🐝 Bee
        "impala": "⧫",         # ⧫ Black diamond
        "sparksql": "⚡",       # ⚡ Lightning
        "spark_sql_query": "⚡",
        "pyspark": "⚡",        # ⚡ Lightning
        "spark_scala": "⚡",
        "sparkr": "⚡",
        "shell": "»",          # » Right guillemet (>>)

        # ML / scoring
        "prediction_scoring": "\U0001f3af",  # 🎯 Target
        "clustering_scoring": "◉",      # ◉ Fish-eye (cluster)
        "evaluation": "✓",              # ✓ Check
        "standalone_evaluation": "✓",
        "ai_assistant_generate": "✨",   # ✨ Sparkles

        "default": "●",        # ● Black circle
    }

    # Text labels for recipe types (Title Case, what shows below an icon).
    LABELS: dict[str, str] = {
        "prepare": "Prepare",
        "join": "Join",
        "fuzzyjoin": "Fuzzy Join",
        "fuzzy_join": "Fuzzy Join",
        "geojoin": "Geo Join",
        "geo_join": "Geo Join",
        "stack": "Stack",
        "grouping": "Grouping",
        "window": "Window",
        "split": "Split",
        "sort": "Sort",
        "distinct": "Distinct",
        "filter": "Filter",
        "python": "Python",
        "r": "R",
        "sync": "Sync",
        "sample": "Sample",
        "sampling": "Sampling",
        "pivot": "Pivot",
        "top_n": "Top N",
        "topn": "Top N",
        "download": "Download",
        "generate_features": "Features",
        "generate_statistics": "Statistics",
        "push_to_editable": "Push",
        "list_folder_contents": "List",
        "dynamic_repeat": "Repeat",
        "extract_failed_rows": "Failed",
        "upsert": "Upsert",
        "list_access": "Access",
        "sql": "SQL",
        "sql_script": "SQL",
        "hive": "Hive",
        "impala": "Impala",
        "sparksql": "Spark SQL",
        "spark_sql_query": "Spark SQL",
        "pyspark": "PySpark",
        "spark_scala": "Spark Scala",
        "sparkr": "SparkR",
        "shell": "Shell",
        "prediction_scoring": "Score",
        "clustering_scoring": "Cluster",
        "evaluation": "Evaluate",
        "standalone_evaluation": "Evaluate",
        "ai_assistant_generate": "AI",
        "default": "Recipe",
    }

    # SVG path icons (24x24 viewBox). Each path is designed to read at icon
    # sizes 14-22px against a colored circle background, and uses
    # `currentColor` via the host renderer's fill attribute.
    SVG_PATHS: dict[str, str] = {
        # PREPARE — gear (FontAwesome `cog` simplified)
        "prepare": (
            "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm9.4 2.6-2-.3a7.5 7.5 0 0 0-.7-1.7"
            "l1.2-1.6a.7.7 0 0 0-.1-.9l-1.4-1.4a.7.7 0 0 0-.9-.1L15.9 5.7"
            "a7.5 7.5 0 0 0-1.7-.7l-.3-2A.7.7 0 0 0 13.2 2.4h-2A.7.7 0 0 0 10.5 3"
            "l-.3 2a7.5 7.5 0 0 0-1.7.7L6.9 4.5a.7.7 0 0 0-.9.1L4.6 6"
            "a.7.7 0 0 0-.1.9l1.2 1.6a7.5 7.5 0 0 0-.7 1.7l-2 .3"
            "a.7.7 0 0 0-.6.7v2c0 .4.3.7.7.8l2 .3c.2.6.4 1.1.7 1.7l-1.2 1.6"
            "a.7.7 0 0 0 .1.9l1.4 1.4a.7.7 0 0 0 .9.1l1.6-1.2"
            "c.5.3 1.1.5 1.7.7l.3 2c0 .4.4.7.8.7h2c.4 0 .7-.3.8-.7l.3-2"
            "c.6-.2 1.2-.4 1.7-.7l1.6 1.2a.7.7 0 0 0 .9-.1l1.4-1.4"
            "a.7.7 0 0 0 .1-.9l-1.2-1.6c.3-.5.5-1.1.7-1.7l2-.3"
            "a.7.7 0 0 0 .6-.8v-2a.7.7 0 0 0-.6-.7z"
        ),
        # JOIN — two overlapping circles (the bowtie / ⋈ glyph as set theory)
        "join": (
            "M9 7a5 5 0 1 0 0 10A5 5 0 0 0 9 7zm6 0a5 5 0 1 0 0 10A5 5 0 0 0 15 7z"
            "M12 8.5a5 5 0 0 1 0 7 5 5 0 0 1 0-7z"
        ),
        # FUZZY_JOIN — overlapping circles with wave outline
        "fuzzyjoin": (
            "M9 7a5 5 0 1 0 0 10A5 5 0 0 0 9 7zm6 0a5 5 0 1 0 0 10A5 5 0 0 0 15 7z"
            "M3 21q1.5-1 3 0t3 0 3 0 3 0 3 0"
        ),
        "fuzzy_join": (
            "M9 7a5 5 0 1 0 0 10A5 5 0 0 0 9 7zm6 0a5 5 0 1 0 0 10A5 5 0 0 0 15 7z"
            "M3 21q1.5-1 3 0t3 0 3 0 3 0 3 0"
        ),
        # GEO_JOIN — pin glyph
        "geojoin": (
            "M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7z"
            "M12 11.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z"
        ),
        "geo_join": (
            "M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7z"
            "M12 11.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z"
        ),
        # GROUPING — Sigma Σ-shaped polyline
        "grouping": (
            "M5 4h14v3l-7 5 7 5v3H5l5-8z"
        ),
        # WINDOW — frame / window
        "window": (
            "M4 4h16v16H4zM4 9h16M9 9v11"
        ),
        # SORT — up/down chevrons
        "sort": (
            "M7 4l-4 5h3v6h2V9h3zM17 20l4-5h-3V9h-2v6h-3z"
        ),
        # DISTINCT — five-point star
        "distinct": (
            "M12 2l2.6 6.3 6.8.5-5.2 4.5 1.6 6.7L12 16.6 6.2 20l1.6-6.7L2.6 8.8"
            "l6.8-.5z"
        ),
        # TOP_N — ranked podium
        "top_n": (
            "M4 20h4v-7H4zm6 0h4V6h-4zm6 0h4v-10h-4z"
        ),
        "topn": (
            "M4 20h4v-7H4zm6 0h4V6h-4zm6 0h4v-10h-4z"
        ),
        # SAMPLING — percent
        "sample": (
            "M19 5L5 19M7 5a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm10 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4z"
        ),
        "sampling": (
            "M19 5L5 19M7 5a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm10 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4z"
        ),
        # STACK — three stacked tiers
        "stack": (
            "M12 3l9 4-9 4-9-4zM3 12l9 4 9-4M3 17l9 4 9-4"
        ),
        # SPLIT — branching arrows (one-to-many)
        "split": (
            "M4 12h6m0 0l-3-3m3 3l-3 3M14 12h6M14 6h6m-6 12h6M14 6l-2 6 2 6"
        ),
        # PIVOT — axis-rotation arrows
        "pivot": (
            "M12 4v6m0 0L7.5 6m4.5 4l4.5-4M12 14v6m0 0l-4.5-4m4.5 4l4.5-4"
        ),
        # SYNC — circular arrows
        "sync": (
            "M4 12a8 8 0 0 1 14-5l2-1v6h-6l2-2A6 6 0 0 0 6 12zm16 0a8 8 0 0 1-14 5"
            "l-2 1v-6h6l-2 2a6 6 0 0 0 10-2z"
        ),
        # PYTHON — interlocking python glyph
        "python": (
            "M12 2c-3 0-5 1.5-5 4v3h5v1H5c-2.5 0-3 2-3 4s.5 4 3 4h2v-3"
            "c0-2 1-3 3-3h4c2 0 3-1 3-3V6c0-2.5-2-4-5-4z"
            "M9 5a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"
            "M12 22c3 0 5-1.5 5-4v-3h-5v-1h7c2.5 0 3-2 3-4s-.5-4-3-4h-2v3"
            "c0 2-1 3-3 3h-4c-2 0-3 1-3 3v3c0 2.5 2 4 5 4z"
            "M15 19a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"
        ),
        # R — letter R inside a circle
        "r": (
            "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM8.5 6.5h4.5"
            "c2.2 0 4 1.5 4 3.5s-1.8 3.5-4 3.5l4 4H14l-3.7-4H10v4H8.5zM10 8v4h2.7c1.3 0 2.3-.9 2.3-2s-1-2-2.3-2z"
        ),
        # SQL — database cylinder
        "sql": (
            "M12 3c4.4 0 8 1.3 8 3v12c0 1.7-3.6 3-8 3s-8-1.3-8-3V6c0-1.7 3.6-3 8-3z"
            "M4 6c0 1.7 3.6 3 8 3s8-1.3 8-3M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"
        ),
        "sql_script": (
            "M12 3c4.4 0 8 1.3 8 3v12c0 1.7-3.6 3-8 3s-8-1.3-8-3V6c0-1.7 3.6-3 8-3z"
            "M4 6c0 1.7 3.6 3 8 3s8-1.3 8-3M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"
        ),
        # HIVE — hexagonal honeycomb
        "hive": (
            "M12 2l8 5v10l-8 5-8-5V7zM12 7l-4 2.5v5L12 17l4-2.5v-5z"
        ),
        # IMPALA — diamond
        "impala": (
            "M12 2l9 10-9 10L3 12z"
        ),
        # PYSPARK / SPARK_SQL / SPARK_SCALA / SPARKR — lightning bolt
        "pyspark": (
            "M14 2L4 14h7l-2 8 11-14h-7z"
        ),
        "sparksql": (
            "M14 2L4 14h7l-2 8 11-14h-7z"
        ),
        "spark_sql_query": (
            "M14 2L4 14h7l-2 8 11-14h-7z"
        ),
        "spark_scala": (
            "M14 2L4 14h7l-2 8 11-14h-7z"
        ),
        "sparkr": (
            "M14 2L4 14h7l-2 8 11-14h-7z"
        ),
        # SHELL — terminal prompt
        "shell": (
            "M3 4h18v16H3zM6 9l3 3-3 3M11 16h6"
        ),
        # GENERATE_STATISTICS — bar chart
        "generate_statistics": (
            "M4 20h16M6 18V8m4 10v-7m4 7V4m4 14v-9"
        ),
        # GENERATE_FEATURES — sparkle / new
        "generate_features": (
            "M12 3l1.6 5.4L19 10l-5.4 1.6L12 17l-1.6-5.4L5 10l5.4-1.6z"
            "M19 16l.7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7z"
        ),
        # PREDICTION_SCORING — target / bullseye
        "prediction_scoring": (
            "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm0 4a6 6 0 1 1 0 12 6 6 0 0 1 0-12z"
            "m0 4a2 2 0 1 1 0 4 2 2 0 0 1 0-4z"
        ),
        # CLUSTERING_SCORING — three-cluster glyph
        "clustering_scoring": (
            "M7 5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z"
            "M17 5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z"
            "M12 14a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z"
        ),
        # EVALUATION — checkmark
        "evaluation": (
            "M5 12l4 4 10-10"
        ),
        "standalone_evaluation": (
            "M5 12l4 4 10-10"
        ),
        # DOWNLOAD — arrow into tray
        "download": (
            "M12 3v10m0 0l-4-4m4 4l4-4M5 18h14"
        ),
        # PUSH_TO_EDITABLE — pencil
        "push_to_editable": (
            "M3 17l11-11 4 4-11 11H3zM14 4l4 4"
        ),
        # DYNAMIC_REPEAT — circular arrows
        "dynamic_repeat": (
            "M4 12a8 8 0 0 1 14-5l2-1v6h-6l2-2A6 6 0 0 0 6 12zm16 0a8 8 0 0 1-14 5"
            "l-2 1v-6h6l-2 2a6 6 0 0 0 10-2z"
        ),
        # EXTRACT_FAILED_ROWS — warning triangle
        "extract_failed_rows": (
            "M12 3l11 18H1zM12 9v6m0 2v.01"
        ),
        # UPSERT — ⇆ glyph
        "upsert": (
            "M3 8h12l-3-3m3 3l-3 3M21 16H9l3-3m-3 3l3 3"
        ),
        # LIST_FOLDER_CONTENTS / LIST_ACCESS — folder
        "list_folder_contents": (
            "M3 7v12h18V9H13l-2-2H3zm0-2h6l2 2h12V5H3z"
        ),
        "list_access": (
            "M3 7v12h18V9H13l-2-2H3zm0-2h6l2 2h12V5H3z"
        ),
        # AI_ASSISTANT_GENERATE — sparkle
        "ai_assistant_generate": (
            "M12 3l1.6 5.4L19 10l-5.4 1.6L12 17l-1.6-5.4L5 10l5.4-1.6z"
        ),
        # FILTER — funnel
        "filter": (
            "M3 5h18l-7 8v6l-4-2v-4z"
        ),

        "default": "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z",
    }

    # ASCII single-character glyphs (terminal-friendly). Wider terminals can
    # render the bracketed forms below; the single-char dict is used for
    # compact / inline rendering.
    GLYPHS: dict[str, str] = {
        "prepare": "⚙",       # ⚙
        "join": "⋈",          # ⋈
        "fuzzyjoin": "≋",     # ≋
        "fuzzy_join": "≋",
        "geojoin": "⌖",       # ⌖
        "geo_join": "⌖",
        "stack": "≡",         # ≡
        "grouping": "Σ",      # Σ
        "window": "▦",        # ▦
        "split": "⑂",         # ⑂
        "sort": "⇅",          # ⇅
        "distinct": "★",      # ★
        "filter": "▼",        # ▼
        "sync": "⇄",          # ⇄
        "sample": "%",        # %
        "sampling": "%",
        "pivot": "⊞",         # ⊞
        "top_n": "↑",         # ↑
        "topn": "↑",
        "download": "⤓",      # ⤓
        "python": "λ",        # λ
        "r": "Ⓡ",             # Ⓡ
        "sql": "§",           # §
        "sql_script": "§",
        "hive": "☸",          # ☸
        "impala": "⧫",        # ⧫
        "pyspark": "⚡",       # ⚡
        "sparksql": "⚡",
        "spark_sql_query": "⚡",
        "spark_scala": "⚡",
        "sparkr": "⚡",
        "shell": "»",         # »
        "generate_statistics": "σ",  # σ
        "generate_features": "✨",    # ✨
        "prediction_scoring": "◉",   # ◉
        "clustering_scoring": "☸",   # ☸
        "evaluation": "✓",    # ✓
        "standalone_evaluation": "✓",
        "ai_assistant_generate": "✨",
        "push_to_editable": "✎",
        "dynamic_repeat": "↻",
        "extract_failed_rows": "⚠",
        "upsert": "⇆",
        "list_folder_contents": "☰",
        "list_access": "☰",
        "default": "●",       # ●
    }

    # Bracketed ASCII representations for terminal rendering (the box-drawing
    # ASCIIVisualizer uses these inside cells).
    ASCII: dict[str, str] = {
        "prepare": "[*]",
        "join": "[><]",
        "fuzzyjoin": "[~~]",
        "fuzzy_join": "[~~]",
        "geojoin": "[@]",
        "geo_join": "[@]",
        "stack": "[=]",
        "grouping": "[E]",
        "window": "[#]",
        "split": "[Y]",
        "sort": "[|]",
        "distinct": "[*]",
        "filter": "[V]",
        "python": "[Py]",
        "r": "[R]",
        "sync": "[<>]",
        "sample": "[%]",
        "sampling": "[%]",
        "pivot": "[+]",
        "top_n": "[^]",
        "topn": "[^]",
        "download": "[v]",
        "sql": "[SQL]",
        "sql_script": "[SQL]",
        "hive": "[Hv]",
        "impala": "[Im]",
        "pyspark": "[~]",
        "sparksql": "[~]",
        "spark_sql_query": "[~]",
        "spark_scala": "[~]",
        "sparkr": "[~]",
        "shell": "[$]",
        "generate_statistics": "[Stats]",
        "generate_features": "[F]",
        "prediction_scoring": "[ML]",
        "clustering_scoring": "[K]",
        "evaluation": "[Ev]",
        "standalone_evaluation": "[Ev]",
        "ai_assistant_generate": "[AI]",
        "push_to_editable": "[Ed]",
        "dynamic_repeat": "[O]",
        "extract_failed_rows": "[!]",
        "upsert": "[U]",
        "list_folder_contents": "[Ls]",
        "list_access": "[Ls]",
        "default": "[?]",
    }

    @staticmethod
    def _normalize(recipe_type: str) -> str:
        return (recipe_type or "default").lower().replace(" ", "_")

    @classmethod
    def get_unicode(cls, recipe_type: str) -> str:
        """Get Unicode icon for recipe type."""
        return cls.UNICODE.get(cls._normalize(recipe_type), cls.UNICODE["default"])

    @classmethod
    def get_glyph(cls, recipe_type: str) -> str:
        """Get a single-character glyph for a recipe type (terminal-safe)."""
        return cls.GLYPHS.get(cls._normalize(recipe_type), cls.GLYPHS["default"])

    @classmethod
    def get_label(cls, recipe_type: str) -> str:
        """Get text label for recipe type."""
        return cls.LABELS.get(cls._normalize(recipe_type), cls.LABELS["default"])

    @classmethod
    def get_ascii(cls, recipe_type: str) -> str:
        """Get bracketed ASCII representation for recipe type."""
        return cls.ASCII.get(cls._normalize(recipe_type), cls.ASCII["default"])

    @classmethod
    def get_svg_path(cls, recipe_type: str) -> str:
        """Get SVG path data (24x24 viewBox) for recipe type."""
        return cls.SVG_PATHS.get(cls._normalize(recipe_type), cls.SVG_PATHS["default"])

    @classmethod
    def coverage(cls) -> int:
        """Number of distinct recipe-type families with a dedicated SVG icon."""
        # De-dupe path strings — alias keys (fuzzy_join / fuzzyjoin) share the
        # same path, but represent the same family.
        return len({v for k, v in cls.SVG_PATHS.items() if k != "default"})
