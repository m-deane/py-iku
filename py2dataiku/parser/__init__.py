"""Python code parsing and analysis."""

from typing import Any, List, Protocol, runtime_checkable

from py2dataiku.parser.ast_analyzer import CodeAnalyzer
from py2dataiku.parser.pattern_matcher import PatternMatcher
from py2dataiku.parser.dataflow_tracker import DataFlowTracker


@runtime_checkable
class AnalyzerProtocol(Protocol):
    """Protocol defining the interface for code analyzers.

    Both rule-based (CodeAnalyzer) and LLM-based (LLMCodeAnalyzer)
    analyzers conform to this protocol.
    """

    def analyze(self, code: str) -> Any:
        """Analyze Python source code and return analysis results."""
        ...


__all__ = [
    "AnalyzerProtocol",
    "CodeAnalyzer",
    "PatternMatcher",
    "DataFlowTracker",
]
