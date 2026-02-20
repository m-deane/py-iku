"""Configuration file support for py2dataiku."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

import yaml


CONFIG_FILE_NAMES = [
    "py2dataiku.toml",
    ".py2dataikurc",
    ".py2dataiku.yaml",
    ".py2dataiku.yml",
]


@dataclass
class Py2DataikuConfig:
    """Configuration settings for py2dataiku."""

    # LLM settings
    default_provider: str = "anthropic"
    default_model: Optional[str] = None
    api_key: Optional[str] = None

    # Project settings
    project_key: str = "MY_PROJECT"
    flow_name: str = "converted_flow"

    # Optimization
    optimize: bool = True
    optimization_level: int = 1  # 0=none, 1=basic, 2=aggressive

    # Naming conventions
    dataset_prefix: str = ""
    dataset_suffix: str = ""
    recipe_prefix: str = ""
    recipe_suffix: str = ""

    # Output
    default_format: str = "svg"
    default_connection: str = "Filesystem"

    # Extra settings
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "provider": {
                "default": self.default_provider,
                "model": self.default_model,
            },
            "project": {
                "key": self.project_key,
                "flow_name": self.flow_name,
            },
            "optimization": {
                "enabled": self.optimize,
                "level": self.optimization_level,
            },
            "naming": {
                "dataset_prefix": self.dataset_prefix,
                "dataset_suffix": self.dataset_suffix,
                "recipe_prefix": self.recipe_prefix,
                "recipe_suffix": self.recipe_suffix,
            },
            "output": {
                "format": self.default_format,
                "connection": self.default_connection,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Py2DataikuConfig":
        """Create config from dictionary."""
        provider = data.get("provider", {})
        project = data.get("project", {})
        optimization = data.get("optimization", {})
        naming = data.get("naming", {})
        output = data.get("output", {})

        return cls(
            default_provider=provider.get("default", "anthropic"),
            default_model=provider.get("model"),
            api_key=provider.get("api_key"),
            project_key=project.get("key", "MY_PROJECT"),
            flow_name=project.get("flow_name", "converted_flow"),
            optimize=optimization.get("enabled", True),
            optimization_level=optimization.get("level", 1),
            dataset_prefix=naming.get("dataset_prefix", ""),
            dataset_suffix=naming.get("dataset_suffix", ""),
            recipe_prefix=naming.get("recipe_prefix", ""),
            recipe_suffix=naming.get("recipe_suffix", ""),
            default_format=output.get("format", "svg"),
            default_connection=output.get("connection", "Filesystem"),
        )


def _load_toml(path: Path) -> Dict[str, Any]:
    """Load a TOML config file."""
    if tomllib is None:
        raise ImportError(
            "TOML support requires Python 3.11+ or the 'tomli' package"
        )
    with open(path, "rb") as f:
        return tomllib.load(f)


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML config file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def find_config_file(
    start_dir: Optional[str] = None,
) -> Optional[Path]:
    """
    Search for a py2dataiku config file.

    Searches in order:
    1. start_dir (or current directory)
    2. Home directory

    Returns the path to the first config file found, or None.
    """
    search_dirs = []
    if start_dir:
        search_dirs.append(Path(start_dir))
    search_dirs.append(Path.cwd())
    search_dirs.append(Path.home())

    for directory in search_dirs:
        for name in CONFIG_FILE_NAMES:
            path = directory / name
            if path.is_file():
                return path
    return None


def load_config(
    config_path: Optional[str] = None,
    auto_discover: bool = True,
) -> Py2DataikuConfig:
    """
    Load py2dataiku configuration.

    Args:
        config_path: Explicit path to config file. If None, auto-discovers.
        auto_discover: Whether to search for config files automatically.

    Returns:
        Py2DataikuConfig with loaded settings, or defaults if no file found.
    """
    if config_path:
        path = Path(config_path)
    elif auto_discover:
        path = find_config_file()
    else:
        path = None

    if path is None:
        return Py2DataikuConfig()

    if not path.exists():
        return Py2DataikuConfig()

    suffix = path.suffix.lower()
    name = path.name.lower()

    if suffix == ".toml" or name == ".py2dataikurc":
        data = _load_toml(path)
    elif suffix in (".yaml", ".yml"):
        data = _load_yaml(path)
    else:
        return Py2DataikuConfig()

    # Allow environment variable overrides
    config = Py2DataikuConfig.from_dict(data)
    env_provider = os.environ.get("PY2DATAIKU_PROVIDER")
    if env_provider:
        config.default_provider = env_provider
    env_key = os.environ.get("PY2DATAIKU_PROJECT_KEY")
    if env_key:
        config.project_key = env_key

    return config
