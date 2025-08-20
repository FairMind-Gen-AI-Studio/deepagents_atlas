# MCP Tools Integration for Atlas V1
# Wrapper functions for Fairmind MCP tools with error handling and retry logic

import logging
import time
from typing import Any, Dict, List, Optional, Union
from functools import wraps

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry MCP calls on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")
            raise last_exception
        return wrapper
    return decorator

class MCPToolsWrapper:
    """Wrapper class for MCP tools with enhanced functionality"""
    
    def __init__(self, tools_dict: Dict[str, Any]):
        """Initialize with available MCP tools"""
        self.tools = tools_dict
        self._extract_tool_functions()
    
    def _extract_tool_functions(self):
        """Extract and categorize MCP tool functions"""
        self.general_tools = {}
        self.studio_tools = {}
        self.code_tools = {}
        
        for tool_name, tool_func in self.tools.items():
            if tool_name.startswith('mcp__fairmind__General_'):
                clean_name = tool_name.replace('mcp__fairmind__General_', '')
                self.general_tools[clean_name] = tool_func
            elif tool_name.startswith('mcp__fairmind__Studio_'):
                clean_name = tool_name.replace('mcp__fairmind__Studio_', '')
                self.studio_tools[clean_name] = tool_func
            elif tool_name.startswith('mcp__fairmind__Code_'):
                clean_name = tool_name.replace('mcp__fairmind__Code_', '')
                self.code_tools[clean_name] = tool_func

    # General Tools - Project and Document Management
    @retry_on_failure()
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all available projects"""
        tool_func = self.general_tools.get('list_projects')
        if not tool_func:
            raise ValueError("General_list_projects tool not available")
        return tool_func.invoke({})
    
    @retry_on_failure()
    def get_document_content(self, document_id: str, start_line: int = 0, end_line: int = 200) -> Dict[str, Any]:
        """Get content of a document by its attachment ID"""
        tool_func = self.general_tools.get('get_document_content')
        if not tool_func:
            raise ValueError("General_get_document_content tool not available")
        return tool_func.invoke({
            'document_id': document_id,
            'start_line': start_line,
            'end_line': end_line
        })
    
    @retry_on_failure()
    def rag_retrieve_documents(self, query: Union[str, List[str]], project_id: str, k: int = 20, score_threshold: float = 0.5) -> Dict[str, Any]:
        """Retrieve documents from RAG by query"""
        tool_func = self.general_tools.get('rag_retrieve_documents')
        if not tool_func:
            raise ValueError("General_rag_retrieve_documents tool not available")
        return tool_func.invoke({
            'query': query,
            'projectId': project_id,
            'k': k,
            'score_threshold': score_threshold
        })

    # Studio Tools - Business Requirements
    @retry_on_failure()
    def list_needs_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """List all needs for a project"""
        tool_func = self.studio_tools.get('list_needs_by_project')
        if not tool_func:
            raise ValueError("Studio_list_needs_by_project tool not available")
        return tool_func.invoke({'project_id': project_id})
    
    @retry_on_failure()
    def get_need(self, need_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific need"""
        tool_func = self.studio_tools.get('get_need')
        if not tool_func:
            raise ValueError("Studio_get_need tool not available")
        return tool_func.invoke({'need_id': need_id})
    
    @retry_on_failure()
    def list_user_stories_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """List all user stories for a project"""
        tool_func = self.studio_tools.get('list_user_stories_by_project')
        if not tool_func:
            raise ValueError("Studio_list_user_stories_by_project tool not available")
        return tool_func.invoke({'project_id': project_id})
    
    @retry_on_failure()
    def list_user_stories_by_need(self, need_id: str) -> List[Dict[str, Any]]:
        """List user stories linked to a specific need"""
        tool_func = self.studio_tools.get('list_user_stories_by_need')
        if not tool_func:
            raise ValueError("Studio_list_user_stories_by_need tool not available")
        return tool_func.invoke({'need_id': need_id})
    
    @retry_on_failure()
    def get_user_story(self, user_story_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific user story"""
        tool_func = self.studio_tools.get('get_user_story')
        if not tool_func:
            raise ValueError("Studio_get_user_story tool not available")
        return tool_func.invoke({'user_story_id': user_story_id})
    
    @retry_on_failure()
    def list_tasks_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """List all tasks for a project"""
        tool_func = self.studio_tools.get('list_tasks_by_project')
        if not tool_func:
            raise ValueError("Studio_list_tasks_by_project tool not available")
        return tool_func.invoke({'project_id': project_id})
    
    @retry_on_failure()
    def list_requirements_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """List all requirements for a project"""
        tool_func = self.studio_tools.get('list_requirements_by_project')
        if not tool_func:
            raise ValueError("Studio_list_requirements_by_project tool not available")
        return tool_func.invoke({'project_id': project_id})

    # Code Tools - Repository Analysis (CRITICAL for Planning Agent)
    @retry_on_failure()
    def list_repositories(self, project_id: str) -> List[Dict[str, Any]]:
        """List all repositories in a project"""
        tool_func = self.code_tools.get('list_repositories')
        if not tool_func:
            raise ValueError("Code_list_repositories tool not available")
        return tool_func.invoke({'project_id': project_id})
    
    @retry_on_failure()
    def get_directory_structure(self, project_id: str, repository_id: str) -> Dict[str, Any]:
        """Get complete directory structure for a repository"""
        tool_func = self.code_tools.get('get_directory_structure')
        if not tool_func:
            raise ValueError("Code_get_directory_structure tool not available")
        return tool_func.invoke({
            'project_id': project_id,
            'repository_id': repository_id
        })
    
    @retry_on_failure()
    def find_relevant_code_snippets(self, query: str, project_id: str, repository_id: Optional[str] = None, top_k: int = 10) -> Dict[str, Any]:
        """Find relevant code snippets using natural language search"""
        tool_func = self.code_tools.get('find_relevant_code_snippets')
        if not tool_func:
            raise ValueError("Code_find_relevant_code_snippets tool not available")
        params = {
            'natural_language_query': query,
            'project_id': project_id,
            'top_k': top_k
        }
        if repository_id:
            params['repository_id'] = repository_id
        return tool_func.invoke(params)
    
    @retry_on_failure()
    def get_file(self, project_id: str, repository_id: str, entity_id: Optional[str] = None, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Get complete content of a specific file"""
        tool_func = self.code_tools.get('get_file')
        if not tool_func:
            raise ValueError("Code_get_file tool not available")
        
        params = {
            'project_id': project_id,
            'repository_id': repository_id
        }
        
        if entity_id:
            params['entity_id'] = entity_id
        elif file_path:
            params['file_path'] = file_path
        else:
            raise ValueError("Either entity_id or file_path must be provided")
        
        return tool_func.invoke(params)
    
    @retry_on_failure()
    def find_usages(self, entity_id: str, project_id: str, repository_id: str) -> Dict[str, Any]:
        """Find all places where a code entity is used"""
        tool_func = self.code_tools.get('find_usages')
        if not tool_func:
            raise ValueError("Code_find_usages tool not available")
        return tool_func.invoke({
            'entity_id': entity_id,
            'project_id': project_id,
            'repository_id': repository_id
        })

    # Helper Methods for Common Workflows
    def investigate_project_context(self, project_id: str, user_story_id: Optional[str] = None) -> Dict[str, Any]:
        """Complete project investigation workflow"""
        context = {
            'projects': [],
            'user_stories': [],
            'needs': [],
            'repositories': [],
            'business_docs': []
        }
        
        try:
            # Get project list if no specific project_id
            if not project_id:
                context['projects'] = self.list_projects()
                if context['projects']:
                    project_id = context['projects'][0].get('project_id')
            
            # Get user stories and needs
            context['user_stories'] = self.list_user_stories_by_project(project_id)
            context['needs'] = self.list_needs_by_project(project_id)
            
            # Get repositories
            context['repositories'] = self.list_repositories(project_id)
            
            # Get business documentation via RAG
            if user_story_id:
                rag_query = f"user story {user_story_id} requirements business context"
                context['business_docs'] = self.rag_retrieve_documents(rag_query, project_id)
            
        except Exception as e:
            logger.error(f"Error in investigate_project_context: {e}")
            context['error'] = str(e)
        
        return context
    
    def analyze_repository_for_story(self, project_id: str, repository_id: str, user_story_description: str) -> Dict[str, Any]:
        """Analyze repository structure and find relevant code for user story"""
        analysis = {
            'structure': {},
            'relevant_code': {},
            'files': {},
            'recommendations': []
        }
        
        try:
            # Get repository structure
            analysis['structure'] = self.get_directory_structure(project_id, repository_id)
            
            # Find relevant code snippets
            analysis['relevant_code'] = self.find_relevant_code_snippets(
                user_story_description, 
                project_id, 
                repository_id, 
                top_k=15
            )
            
            # Analyze key files if relevant code found
            if analysis['relevant_code'].get('results'):
                for result in analysis['relevant_code']['results'][:5]:  # Top 5 results
                    if 'entity_id' in result:
                        try:
                            file_content = self.get_file(project_id, repository_id, entity_id=result['entity_id'])
                            analysis['files'][result.get('file_path', 'unknown')] = file_content
                        except Exception as e:
                            logger.warning(f"Could not get file for entity {result['entity_id']}: {e}")
            
        except Exception as e:
            logger.error(f"Error in analyze_repository_for_story: {e}")
            analysis['error'] = str(e)
        
        return analysis

    def get_available_tools(self) -> Dict[str, List[str]]:
        """Get list of available tools by category"""
        return {
            'general_tools': list(self.general_tools.keys()),
            'studio_tools': list(self.studio_tools.keys()),
            'code_tools': list(self.code_tools.keys())
        }

# Factory function to create MCP tools wrapper from available tools
def create_mcp_wrapper(available_tools: Dict[str, Any]) -> MCPToolsWrapper:
    """Create MCP tools wrapper from available tools dictionary"""
    return MCPToolsWrapper(available_tools)