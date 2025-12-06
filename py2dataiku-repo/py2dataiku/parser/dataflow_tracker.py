"""Track data lineage through Python code."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class DataFrameState:
    """State of a DataFrame at a point in the code."""

    variable_name: str
    columns: List[str] = field(default_factory=list)
    source: Optional[str] = None  # Original data source
    transformations: List[str] = field(default_factory=list)
    line_number: int = 0


class DataFlowTracker:
    """
    Track DataFrame lineage and transformations through code.

    This class maintains state about DataFrames as they are
    transformed throughout the code, enabling column lineage tracking.
    """

    def __init__(self):
        self.states: Dict[str, DataFrameState] = {}
        self.aliases: Dict[str, str] = {}  # variable aliases

    def register_read(
        self,
        variable: str,
        source: str,
        columns: Optional[List[str]] = None,
        line: int = 0,
    ) -> None:
        """Register a data read operation."""
        self.states[variable] = DataFrameState(
            variable_name=variable,
            columns=columns or [],
            source=source,
            line_number=line,
        )

    def register_transformation(
        self,
        source_var: str,
        target_var: str,
        transformation: str,
        line: int = 0,
    ) -> None:
        """Register a transformation operation."""
        if source_var in self.states:
            source_state = self.states[source_var]
            new_state = DataFrameState(
                variable_name=target_var,
                columns=source_state.columns.copy(),
                source=source_state.source,
                transformations=source_state.transformations + [transformation],
                line_number=line,
            )
            self.states[target_var] = new_state

            # Track alias if same variable
            if source_var == target_var:
                pass
            else:
                self.aliases[target_var] = source_var

    def register_column_add(
        self,
        variable: str,
        column: str,
        line: int = 0,
    ) -> None:
        """Register a new column being added."""
        if variable in self.states:
            if column not in self.states[variable].columns:
                self.states[variable].columns.append(column)
            self.states[variable].transformations.append(f"add_column:{column}")

    def register_column_drop(
        self,
        variable: str,
        columns: List[str],
        line: int = 0,
    ) -> None:
        """Register columns being dropped."""
        if variable in self.states:
            for col in columns:
                if col in self.states[variable].columns:
                    self.states[variable].columns.remove(col)
            self.states[variable].transformations.append(
                f"drop_columns:{','.join(columns)}"
            )

    def register_column_rename(
        self,
        variable: str,
        mapping: Dict[str, str],
        line: int = 0,
    ) -> None:
        """Register column renames."""
        if variable in self.states:
            for old, new in mapping.items():
                if old in self.states[variable].columns:
                    idx = self.states[variable].columns.index(old)
                    self.states[variable].columns[idx] = new
            self.states[variable].transformations.append(
                f"rename:{','.join(f'{k}->{v}' for k, v in mapping.items())}"
            )

    def register_merge(
        self,
        left_var: str,
        right_var: str,
        target_var: str,
        on: Optional[List[str]] = None,
        line: int = 0,
    ) -> None:
        """Register a merge/join operation."""
        columns = []
        if left_var in self.states:
            columns.extend(self.states[left_var].columns)
        if right_var in self.states:
            # Add columns from right that aren't in left
            for col in self.states[right_var].columns:
                if col not in columns or col in (on or []):
                    columns.append(col)

        self.states[target_var] = DataFrameState(
            variable_name=target_var,
            columns=columns,
            source=f"merge({left_var}, {right_var})",
            transformations=[f"merge:{left_var}+{right_var}"],
            line_number=line,
        )

    def get_state(self, variable: str) -> Optional[DataFrameState]:
        """Get the current state of a variable."""
        return self.states.get(variable)

    def get_columns(self, variable: str) -> List[str]:
        """Get the columns for a variable."""
        state = self.get_state(variable)
        return state.columns if state else []

    def get_lineage(self, variable: str) -> List[str]:
        """Get the transformation lineage for a variable."""
        state = self.get_state(variable)
        return state.transformations if state else []

    def get_source(self, variable: str) -> Optional[str]:
        """Get the original data source for a variable."""
        state = self.get_state(variable)
        return state.source if state else None

    def resolve_alias(self, variable: str) -> str:
        """Resolve variable aliases to the original variable."""
        while variable in self.aliases:
            variable = self.aliases[variable]
        return variable
