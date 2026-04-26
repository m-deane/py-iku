"""Pydantic v2 schemas for catalog endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .processor import ProcessorTypeEnum
from .recipe import RecipeTypeEnum


class RecipeCatalogEntry(BaseModel):
    """A single entry in the recipe catalog."""

    type: RecipeTypeEnum
    name: str = Field(..., description="Human-readable recipe name")
    category: str = Field(..., description="Recipe category (e.g. Visual, Code, ML)")
    icon: str = Field(..., description="Unicode or ASCII icon character")
    description: str = Field(..., description="Short description of the recipe")
    pandas_examples: list[str] = Field(
        default_factory=list, description="pandas patterns that map to this recipe"
    )


class ProcessorCatalogEntry(BaseModel):
    """A single entry in the processor catalog (from ProcessorCatalog.get_processor)."""

    type: ProcessorTypeEnum | str = Field(
        ..., description="ProcessorType enum value"
    )
    name: str = Field(..., description="DSS processor name (canonical)")
    category: str = Field(..., description="Processor category")
    description: str = Field(..., description="Short description")
    required_params: list[str] = Field(default_factory=list)
    optional_params: list[str] = Field(default_factory=list)
    examples: dict[str, Any] = Field(
        default_factory=dict, description="Example parameter values"
    )
