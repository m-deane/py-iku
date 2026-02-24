"""Integrations for py2dataiku.

This module provides integration bridges for deploying py2dataiku flows
to Dataiku DSS instances, either via the dataikuapi Python client or
via MCP (Model Context Protocol) tool call generation.

Usage:
    >>> from py2dataiku.integrations import DSSFlowDeployer, generate_mcp_tool_calls
    >>> deployer = DSSFlowDeployer("https://dss.example.com", "api_key", "MY_PROJECT")
    >>> result = deployer.deploy(flow)
    >>>
    >>> tool_calls = generate_mcp_tool_calls(flow, "MY_PROJECT")
"""

from py2dataiku.integrations.dss_client import DSSFlowDeployer, DeploymentResult
from py2dataiku.integrations.mcp_tools import generate_mcp_tool_calls, format_mcp_script

__all__ = [
    "DSSFlowDeployer",
    "DeploymentResult",
    "generate_mcp_tool_calls",
    "format_mcp_script",
]
