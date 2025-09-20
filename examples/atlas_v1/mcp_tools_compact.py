# Compact MCP Tools for Atlas V1
# Ultra-simplified implementation following DeepAgents patterns
# Target: <150 lines total

import logging
from typing import Any, Dict, List, Optional
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Global MCP tools storage
_mcp_tools: Optional[Dict[str, Any]] = None

def init_mcp(tools_dict: Optional[Dict[str, Any]]) -> None:
    """Initialize MCP tools"""
    global _mcp_tools
    _mcp_tools = tools_dict or {}
    logger.info(f"MCP initialized: {len(_mcp_tools)} tools")

async def _call_mcp_async(name: str, **params) -> Any:
    """Async MCP tool caller"""
    if not _mcp_tools:
        return [] if params else {}

    # Try different naming patterns
    for prefix in ['General_', 'Studio_', 'Code_', '']:
        tool = _mcp_tools.get(f"{prefix}{name}")
        if tool:
            try:
                # Use async invocation if available, otherwise use sync with proper handling
                if hasattr(tool, 'ainvoke'):
                    return await tool.ainvoke(params)
                elif hasattr(tool, 'invoke'):
                    # For sync invocation, we need to handle the event loop issue
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # We're in an async context, need to run in executor
                            return await loop.run_in_executor(None, lambda: tool.invoke(params))
                        else:
                            return tool.invoke(params)
                    except RuntimeError:
                        # No event loop, create one
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(tool.ainvoke(params)) if hasattr(tool, 'ainvoke') else tool.invoke(params)
                        finally:
                            loop.close()
                else:
                    logger.error(f"No invoke method found for tool {name}")
                    return [] if 'list' in name else {}
            except Exception as e:
                logger.error(f"MCP error in {name}: {e}")
                break
    return [] if 'list' in name else {}

def _call_mcp(name: str, **params) -> Any:
    """Sync wrapper for async MCP tool caller"""
    import asyncio
    try:
        # Try to get current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, run in executor
            return loop.run_until_complete(_call_mcp_async(name, **params))
        else:
            # Not in async context, create new loop
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(_call_mcp_async(name, **params))
            finally:
                new_loop.close()
    except RuntimeError:
        # No event loop available, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_call_mcp_async(name, **params))
        finally:
            loop.close()

# ============= General Tools =============

@tool
def list_projects() -> List[Dict]:
    """List all projects"""
    return _call_mcp("list_projects") or []

@tool  
def get_document_content(document_id: str, start_line: int = 0, end_line: int = 200) -> str:
    """Get document content"""
    return _call_mcp("get_document_content", 
                     document_id=document_id, 
                     start_line=start_line, 
                     end_line=end_line) or ""

@tool
def rag_retrieve_documents(query: str, project_id: Optional[str] = None, k: int = 20) -> List[Dict]:
    """Search documents using RAG"""
    params = {"query": query, "k": k}
    if project_id:
        params["projectId"] = project_id
    return _call_mcp("rag_retrieve_documents", **params) or []

# ============= Studio Tools =============

@tool
def list_user_stories_by_project(project_id: str) -> List[Dict]:
    """List user stories for project"""
    return _call_mcp("list_user_stories_by_project", project_id=project_id) or []

@tool
def get_user_story(user_story_id: str) -> Dict:
    """Get user story details"""
    return _call_mcp("get_user_story", user_story_id=user_story_id) or {}

@tool
def list_needs_by_project(project_id: str) -> List[Dict]:
    """List project needs"""
    return _call_mcp("list_needs_by_project", project_id=project_id) or []

@tool
def get_need(need_id: str) -> Dict:
    """Get need details"""
    return _call_mcp("get_need", need_id=need_id) or {}

@tool
def list_tasks_by_project(project_id: str) -> List[Dict]:
    """List project tasks"""
    return _call_mcp("list_tasks_by_project", project_id=project_id) or []

@tool
def list_requirements_by_project(project_id: str) -> List[Dict]:
    """List project requirements"""
    return _call_mcp("list_requirements_by_project", project_id=project_id) or []

# ============= Code Tools =============

@tool
def list_repositories(project_id: str) -> List[Dict]:
    """List project repositories"""
    return _call_mcp("list_repositories", project_id=project_id) or []

@tool
def get_directory_structure(project_id: str, repository_id: str) -> Dict:
    """Get repository structure"""
    return _call_mcp("get_directory_structure", 
                     project_id=project_id, 
                     repository_id=repository_id) or {}

@tool
def find_relevant_code_snippets(natural_language_query: str, project_id: str, 
                                repository_id: Optional[str] = None, top_k: int = 10) -> Dict:
    """Find code snippets"""
    params = {"natural_language_query": natural_language_query, "project_id": project_id, "top_k": top_k}
    if repository_id:
        params["repository_id"] = repository_id
    return _call_mcp("find_relevant_code_snippets", **params) or {}

@tool
def get_file(project_id: str, repository_id: str, 
            entity_id: Optional[str] = None, file_path: Optional[str] = None) -> Dict:
    """Get file content"""
    if not entity_id and not file_path:
        return {"error": "Need entity_id or file_path"}
    params = {"project_id": project_id, "repository_id": repository_id}
    if entity_id:
        params["entity_id"] = entity_id
    if file_path:
        params["file_path"] = file_path
    return _call_mcp("get_file", **params) or {}

@tool
def find_usages(project_id: str, repository_id: str, entity_id: str) -> Dict:
    """Find entity usages"""
    return _call_mcp("find_usages", 
                     project_id=project_id, 
                     repository_id=repository_id, 
                     entity_id=entity_id) or {}

# ============= Tool Collections =============

def get_all_mcp_tools() -> List:
    """Get all MCP tools"""
    return [
        list_projects, get_document_content, rag_retrieve_documents,
        list_user_stories_by_project, get_user_story, list_needs_by_project,
        get_need, list_tasks_by_project, list_requirements_by_project,
        list_repositories, get_directory_structure, find_relevant_code_snippets,
        get_file, find_usages
    ]

def get_general_tools() -> List:
    """Get General MCP tools"""
    return [list_projects, get_document_content, rag_retrieve_documents]

def get_studio_tools() -> List:
    """Get Studio MCP tools"""
    return [list_user_stories_by_project, get_user_story, list_needs_by_project,
            get_need, list_tasks_by_project, list_requirements_by_project]

def get_code_tools() -> List:
    """Get Code MCP tools"""
    return [list_repositories, get_directory_structure, find_relevant_code_snippets,
            get_file, find_usages]