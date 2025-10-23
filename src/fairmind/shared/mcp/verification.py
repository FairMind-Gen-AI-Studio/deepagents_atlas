"""
MCP Tool Verification and Logging Utilities

Provides comprehensive tool verification and startup logging for Fairmind agents.
Helps debug tool assignment issues and ensures critical tools are available.
"""

import logging
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)


def categorize_tools(tools_dict: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Categorize MCP tools by prefix (General, Studio, Code).

    Args:
        tools_dict: Dictionary of MCP tools {name: tool_object}

    Returns:
        Dictionary with categorized tool names {category: [tool_names]}
    """
    categories = {
        "General": [],
        "Studio": [],
        "Code": [],
        "Other": []
    }

    for name in tools_dict.keys():
        if "General_" in name:
            categories["General"].append(name)
        elif "Studio_" in name:
            categories["Studio"].append(name)
        elif "Code_" in name:
            categories["Code"].append(name)
        else:
            categories["Other"].append(name)

    return categories


def check_tool_name_consistency(tools_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for tool name prefix inconsistencies.

    Detects if tools use different naming patterns (with/without mcp__fairmind__ prefix).

    Args:
        tools_dict: Dictionary of MCP tools

    Returns:
        Dictionary with consistency analysis
    """
    prefixed = []
    non_prefixed = []

    for name in tools_dict.keys():
        if name.startswith("mcp__fairmind__"):
            prefixed.append(name)
        elif any(name.startswith(prefix) for prefix in ["General_", "Studio_", "Code_"]):
            non_prefixed.append(name)

    has_both = len(prefixed) > 0 and len(non_prefixed) > 0

    return {
        "has_prefixed": len(prefixed) > 0,
        "has_non_prefixed": len(non_prefixed) > 0,
        "has_mixed_naming": has_both,
        "prefixed_count": len(prefixed),
        "non_prefixed_count": len(non_prefixed),
        "prefixed_samples": prefixed[:3] if prefixed else [],
        "non_prefixed_samples": non_prefixed[:3] if non_prefixed else [],
    }


def verify_tool_availability(
    tools_dict: Dict[str, Any],
    required_tools: List[str],
    agent_name: str
) -> List[str]:
    """
    Verify that required tools are available.

    Handles both naming conventions (prefixed and non-prefixed).

    Args:
        tools_dict: Dictionary of available MCP tools
        required_tools: List of required tool names
        agent_name: Name of agent for logging

    Returns:
        List of missing tool names (empty if all present)
    """
    if not tools_dict:
        logger.warning(f"⚠️  [{agent_name}] No MCP tools available - cannot verify requirements")
        return required_tools

    missing = []

    for required in required_tools:
        # Check for both naming variants
        found = False
        for actual_name in tools_dict.keys():
            if required in actual_name or actual_name.endswith(required):
                found = True
                break

        if not found:
            missing.append(required)

    if missing:
        logger.warning(f"⚠️  [{agent_name}] Missing required tools: {missing}")
        logger.warning(f"   Available tools: {list(tools_dict.keys())[:5]}...")

    return missing


def create_tool_report(tools_dict: Dict[str, Any]) -> str:
    """
    Generate comprehensive tool inventory report.

    Args:
        tools_dict: Dictionary of MCP tools

    Returns:
        Formatted report string
    """
    if not tools_dict:
        return "❌ No MCP tools available"

    categories = categorize_tools(tools_dict)
    consistency = check_tool_name_consistency(tools_dict)

    report_lines = [
        f"✅ MCP tools initialized: {len(tools_dict)} tools available",
        "",
        "Tool Distribution:"
    ]

    # Add categorized tools
    for category, tools in categories.items():
        if tools:
            report_lines.append(f"  - {category}: {len(tools)} tools")
            # Show first 3 tools as examples
            for tool_name in tools[:3]:
                # Strip mcp__fairmind__ prefix for cleaner display
                clean_name = tool_name.replace("mcp__fairmind__", "")
                report_lines.append(f"      ✓ {clean_name}")
            if len(tools) > 3:
                report_lines.append(f"      ... ({len(tools) - 3} more)")

    # Add consistency warning if needed
    if consistency["has_mixed_naming"]:
        report_lines.extend([
            "",
            "⚠️  Tool Name Variants Detected:",
            "   Some tools use mcp__fairmind__ prefix, others don't",
            "   Filtering handles both automatically"
        ])

    return "\n".join(report_lines)


def log_tool_assignment(
    agent_name: str,
    tools: List[Any],
    critical_tools: Optional[List[str]] = None
) -> None:
    """
    Log comprehensive tool assignment information for an agent.

    Args:
        agent_name: Name of the agent
        tools: List of tool objects assigned to agent
        critical_tools: Optional list of critical tool names to verify
    """
    tool_count = len(tools)

    if tool_count == 0:
        logger.info(f"  - {agent_name}: 0 MCP tools (filesystem only)")
        return

    # Get tool names
    tool_names = [getattr(t, 'name', str(t)) for t in tools]

    # Categorize assigned tools
    categories = {
        "General": [n for n in tool_names if "General_" in n],
        "Studio": [n for n in tool_names if "Studio_" in n],
        "Code": [n for n in tool_names if "Code_" in n],
    }

    category_status = []
    for category, cat_tools in categories.items():
        if cat_tools:
            category_status.append(f"{category}: ✅")

    logger.info(f"  - {agent_name}: {tool_count} MCP tools")
    if category_status:
        logger.info(f"      Has {', '.join(category_status)}")

    # Show tool examples
    if len(tool_names) <= 5:
        for name in tool_names:
            clean_name = name.replace("mcp__fairmind__", "")
            logger.info(f"      ✓ {clean_name}")
    else:
        for name in tool_names[:3]:
            clean_name = name.replace("mcp__fairmind__", "")
            logger.info(f"      ✓ {clean_name}")
        logger.info(f"      ... ({len(tool_names) - 3} more)")

    # Verify critical tools if specified
    if critical_tools:
        missing_critical = []
        for critical in critical_tools:
            found = any(critical in name for name in tool_names)
            if not found:
                missing_critical.append(critical)

        if missing_critical:
            logger.warning(f"      ⚠️  Missing critical tools: {missing_critical}")
        else:
            logger.info(f"      Critical tools: ✅ All present")


def verify_phase_tools(
    phase_name: str,
    assigned_tools: List[Any],
    required_tool_names: List[str]
) -> Dict[str, Any]:
    """
    Verify that a phase has all required tools assigned.

    Args:
        phase_name: Name of the phase
        assigned_tools: List of tool objects assigned to phase
        required_tool_names: List of required tool names

    Returns:
        Verification result dictionary
    """
    tool_names = [getattr(t, 'name', str(t)) for t in assigned_tools]

    missing = []
    for required in required_tool_names:
        found = any(required in name for name in tool_names)
        if not found:
            missing.append(required)

    result = {
        "phase": phase_name,
        "tools_assigned": len(assigned_tools),
        "tools_required": len(required_tool_names),
        "all_present": len(missing) == 0,
        "missing_tools": missing,
    }

    if missing:
        logger.error(f"❌ [{phase_name}] Missing required tools: {missing}")
        logger.error(f"   Required: {required_tool_names}")
        logger.error(f"   Assigned: {[n.replace('mcp__fairmind__', '') for n in tool_names]}")
    else:
        logger.debug(f"✅ [{phase_name}] All required tools present")

    return result


def log_agent_startup(
    agent_name: str,
    mcp_tools: Optional[Dict[str, Any]],
    phase_assignments: Dict[str, List[Any]],
    critical_tools_per_phase: Optional[Dict[str, List[str]]] = None
) -> None:
    """
    Log comprehensive agent startup information.

    This is a convenience function that combines tool report and phase assignments
    into a single, well-formatted startup log.

    Args:
        agent_name: Name of the agent
        mcp_tools: Dictionary of all available MCP tools
        phase_assignments: Dictionary mapping phase names to assigned tools
        critical_tools_per_phase: Optional dict mapping phase names to critical tool lists
    """
    logger.info("=" * 70)
    logger.info(f"{agent_name.upper()} - MCP TOOLS VERIFICATION")
    logger.info("=" * 70)
    logger.info("")

    if mcp_tools:
        logger.info(create_tool_report(mcp_tools))
        logger.info("")
        logger.info("Agent Phase Tool Assignments:")

        for phase_name, tools in phase_assignments.items():
            critical = critical_tools_per_phase.get(phase_name) if critical_tools_per_phase else None
            log_tool_assignment(phase_name, tools, critical)

    else:
        logger.warning("⚠️  NO MCP tools available")
        logger.warning("   Agents will use only built-in tools")
        logger.warning("   Check: FAIRMIND_MCP_URL and FAIRMIND_MCP_TOKEN environment variables")

    logger.info("")
    logger.info("=" * 70)
