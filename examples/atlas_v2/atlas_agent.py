# Atlas V2 Agent - Simplified Architecture
# Clean implementation following research pattern
# 4-phase methodology with minimal complexity

"""
Atlas V2 Agent - Simplified 4-phase methodology

This implementation follows the research pattern:
- Single main file with sub-agents
- Direct use of create_deep_agent
- Built-in DeepAgents tools + MCP FairMind tools
- Only Anthropic models
- No custom state management
- LangGraph API compatible

Phases:
1. Investigation - Silent project exploration
2. Discussion - Interactive requirements clarification
3. Planning - Repository analysis and solution design
4. Task Generation - Create actionable tasks
"""

import os
from typing import Literal
from deepagents import create_deep_agent

# ===== PLACEHOLDER MCP TOOLS =====
# These are placeholder functions that simulate ALL MCP FairMind tools functionality
# In a real implementation, these would connect to the FairMind MCP server

# ===== GENERAL TOOLS =====
def general_list_projects():
    """List all projects accessible to the user"""
    return {
        "success": True,
        "message": "This is a placeholder for mcp_FairMind_General_list_projects",
        "data": [
            {"id": "proj-1", "name": "Example Project 1"},
            {"id": "proj-2", "name": "Example Project 2"}
        ]
    }

def general_list_user_attachments_by_project(project_id: str):
    """List user attachments by project"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_General_list_user_attachments_by_project (Project: {project_id})",
        "data": [
            {"id": "att-1", "name": "attachment1.pdf", "project_id": project_id},
            {"id": "att-2", "name": "attachment2.docx", "project_id": project_id}
        ]
    }

def general_get_document_content(document_id: str):
    """Get document content by ID"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_General_get_document_content (ID: {document_id})",
        "data": f"Content of document {document_id}"
    }

def general_rag_retrieve_documents(query: str):
    """RAG retrieve documents"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_General_rag_retrieve_documents (Query: {query})",
        "data": [
            {"id": "doc-1", "title": "Document 1", "relevance": 0.9},
            {"id": "doc-2", "title": "Document 2", "relevance": 0.8}
        ]
    }

def general_rag_retrieve_specific_documents(document_ids: list):
    """RAG retrieve specific documents"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_General_rag_retrieve_specific_documents (IDs: {document_ids})",
        "data": [
            {"id": doc_id, "title": f"Document {doc_id}", "content": f"Content for document {doc_id}"}
            for doc_id in document_ids
        ]
    }

# ===== STUDIO TOOLS =====
def studio_list_needs_by_project(project_id: str):
    """List needs by project"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Studio_list_needs_by_project (Project: {project_id})",
        "data": [
            {"id": "need-1", "title": "Need 1", "project_id": project_id},
            {"id": "need-2", "title": "Need 2", "project_id": project_id}
        ]
    }

def studio_get_need(need_id: str):
    """Get need by ID"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Studio_get_need (ID: {need_id})",
        "data": {
            "id": need_id,
            "title": f"Need {need_id}",
            "description": f"Description for need {need_id}"
        }
    }

def studio_list_user_stories_by_project(project_id: str):
    """List user stories by project"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Studio_list_user_stories_by_project (Project: {project_id})",
        "data": [
            {"id": "story-1", "title": "User Story 1", "project_id": project_id},
            {"id": "story-2", "title": "User Story 2", "project_id": project_id}
        ]
    }

def studio_list_user_stories_by_need(need_id: str):
    """List user stories by need"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Studio_list_user_stories_by_need (Need: {need_id})",
        "data": [
            {"id": "story-1", "title": "User Story 1", "need_id": need_id},
            {"id": "story-2", "title": "User Story 2", "need_id": need_id}
        ]
    }

def studio_list_user_stories_by_role(role_id: str):
    """List user stories by role"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Studio_list_user_stories_by_role (Role: {role_id})",
        "data": [
            {"id": "story-1", "title": "User Story 1", "role_id": role_id},
            {"id": "story-2", "title": "User Story 2", "role_id": role_id}
        ]
    }

def studio_get_user_story(story_id: str):
    """Get user story by ID"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Studio_get_user_story (ID: {story_id})",
        "data": {
            "id": story_id,
            "title": f"User Story {story_id}",
            "description": f"Description for user story {story_id}"
        }
    }

def studio_get_related_user_stories(story_id: str):
    """Get related user stories"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Studio_get_related_user_stories (Story: {story_id})",
        "data": [
            {"id": "related-1", "title": "Related Story 1"},
            {"id": "related-2", "title": "Related Story 2"}
        ]
    }

def studio_list_tasks_by_project(project_id: str):
    """List tasks by project"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Studio_list_tasks_by_project (Project: {project_id})",
        "data": [
            {"id": "task-1", "title": "Task 1", "project_id": project_id},
            {"id": "task-2", "title": "Task 2", "project_id": project_id}
        ]
    }

def studio_get_task(task_id: str):
    """Get task by ID"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Studio_get_task (ID: {task_id})",
        "data": {
            "id": task_id,
            "title": f"Task {task_id}",
            "description": f"Description for task {task_id}"
        }
    }

def studio_list_requirements_by_project(project_id: str):
    """List requirements by project"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Studio_list_requirements_by_project (Project: {project_id})",
        "data": [
            {"id": "req-1", "title": "Requirement 1", "project_id": project_id},
            {"id": "req-2", "title": "Requirement 2", "project_id": project_id}
        ]
    }

def studio_get_requirement(requirement_id: str):
    """Get requirement by ID"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Studio_get_requirement (ID: {requirement_id})",
        "data": {
            "id": requirement_id,
            "title": f"Requirement {requirement_id}",
            "description": f"Description for requirement {requirement_id}"
        }
    }

def studio_list_tests_by_userstory(story_id: str):
    """List tests by user story"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Studio_list_tests_by_userstory (Story: {story_id})",
        "data": [
            {"id": "test-1", "title": "Test 1", "story_id": story_id},
            {"id": "test-2", "title": "Test 2", "story_id": story_id}
        ]
    }

def studio_list_tests_by_project(project_id: str):
    """List tests by project"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Studio_list_tests_by_project (Project: {project_id})",
        "data": [
            {"id": "test-1", "title": "Test 1", "project_id": project_id},
            {"id": "test-2", "title": "Test 2", "project_id": project_id}
        ]
    }

# ===== CODE TOOLS =====
def code_list_repositories():
    """List repositories"""
    return {
        "success": True,
        "message": "Placeholder for mcp_FairMind_Code_list_repositories",
        "data": [
            {"id": "repo-1", "name": "Repository 1"},
            {"id": "repo-2", "name": "Repository 2"}
        ]
    }

def code_get_directory_structure(repository_id: str):
    """Get directory structure"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Code_get_directory_structure (Repo: {repository_id})",
        "data": {
            "structure": "src/\n  components/\n  utils/\n  tests/\nREADME.md\npackage.json"
        }
    }

def code_find_relevant_code_snippets(query: str):
    """Find relevant code snippets"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Code_find_relevant_code_snippets (Query: {query})",
        "data": [
            {"file": "src/main.py", "snippet": f"Code snippet related to {query}"},
            {"file": "src/utils.py", "snippet": f"Another snippet for {query}"}
        ]
    }

def code_find_usages(symbol: str):
    """Find usages of a symbol"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Code_find_usages (Symbol: {symbol})",
        "data": [
            {"file": "src/main.py", "line": 10, "usage": f"Usage of {symbol}"},
            {"file": "src/utils.py", "line": 25, "usage": f"Another usage of {symbol}"}
        ]
    }

def code_get_file(file_path: str):
    """Get file content"""
    return {
        "success": True,
        "message": f"Placeholder for mcp_FairMind_Code_get_file (Path: {file_path})",
        "data": {
            "path": file_path,
            "content": f"Content of file {file_path}"
        }
    }

# ===== ALL MCP FAIRMIND TOOLS =====
MCP_FAIRMIND_TOOLS = [
    # General Tools
    general_list_projects,
    general_list_user_attachments_by_project,
    general_get_document_content,
    general_rag_retrieve_documents,
    general_rag_retrieve_specific_documents,

    # Studio Tools
    studio_list_needs_by_project,
    studio_get_need,
    studio_list_user_stories_by_project,
    studio_list_user_stories_by_need,
    studio_list_user_stories_by_role,
    studio_get_user_story,
    studio_get_related_user_stories,
    studio_list_tasks_by_project,
    studio_get_task,
    studio_list_requirements_by_project,
    studio_get_requirement,
    studio_list_tests_by_userstory,
    studio_list_tests_by_project,

    # Code Tools
    code_list_repositories,
    code_get_directory_structure,
    code_find_relevant_code_snippets,
    code_find_usages,
    code_get_file,
]


# ===== INVESTIGATION AGENT =====
investigation_prompt = """You are the Investigation Agent. Your job is to gather project context using MCP tools.

## CRITICAL: START WITH MCP TOOLS

**DO THIS FIRST - NO EXCEPTIONS:**

1. Call studio_list_projects() → get project_id
2. Call studio_list_user_stories_by_project(project_id) → get user stories
3. Call studio_get_user_story(story_id) → get story details
4. Call studio_get_need(need_id) → get business need
5. Call studio_get_related_user_stories(story_id) → get related stories

## Your MCP Tools
- studio_list_projects()
- studio_list_user_stories_by_project(project_id)
- studio_get_user_story(story_id)
- studio_get_need(need_id)
- studio_get_related_user_stories(story_id)
- studio_list_needs_by_project(project_id)
- general_get_document_content(document_id)
- code_get_file(file_path)

## Simple Workflow
1. Use MCP tools to get ALL context
2. Write findings to investigation_findings.md
3. That's it - no file reading needed

## Example
```python
projects = studio_list_projects()
stories = studio_list_user_stories_by_project(projects['data'][0]['id'])
story = studio_get_user_story(stories['data'][0]['id'])
need = studio_get_need(story['data']['need_id'])
related = studio_get_related_user_stories(stories['data'][0]['id'])
write_file('investigation_findings.md', 'Project context gathered')
```"""

investigation_agent = {
    "name": "investigation-agent",
    "description": "Phase 1: Autonomous project exploration and context gathering",
    "prompt": investigation_prompt,
    "tools": [
        "studio_list_projects",
        "studio_list_user_stories_by_project",
        "studio_get_user_story",
        "studio_get_need",
        "studio_get_related_user_stories",
        "studio_list_needs_by_project",
        "general_get_document_content",
        "code_get_file",
    ]
}


# ===== DISCUSSION AGENT =====
discussion_prompt = """You are the Discussion Agent for Phase 2 of the Atlas methodology.

Your role is to engage the user in targeted discussion to clarify requirements and resolve knowledge gaps identified during investigation.

## Mission
Generate and ask focused clarification questions based on the investigation findings, then synthesize user responses into clear, approved requirements.

## Available Tools
You have access to these tools:
- human_input - Ask questions to the user
- approve_plan - Get approval on requirements
- MCP FairMind tools for verification:
  - studio_list_projects() - List all accessible projects
  - studio_list_user_stories_by_project(project_id) - Get user stories for a project
  - studio_get_user_story(story_id) - Get detailed user story information
  - studio_get_need(need_id) - Get business need details
  - studio_list_needs_by_project(project_id) - Get needs for a project
  - general_get_document_content(document_id) - Get document content
  - code_get_file(file_path) - Get file content from repositories

## Key Rules
- ONLY ask business/functional questions (no technical implementation details)
- Questions must fit categories: CLARIFICATION, DISAMBIGUATION, INTEGRATION, CONTEXT, CONFLICT RESOLUTION
- Maximum 5-7 questions per round
- Use MCP tools to verify information before asking questions
- Make reasonable inferences for non-critical details

## Discussion Workflow

1. Review Investigation Findings
   - Read investigation_findings.md to understand current context
   - Use MCP tools to verify any unclear information:
     * Call studio_get_user_story(story_id) for user story details
     * Call studio_get_need(need_id) for business need context
     * Call general_get_document_content(doc_id) for referenced documents
   - Identify critical knowledge gaps that need user clarification

2. Generate Business Questions
   - Focus only on business requirements, user experience, and functional needs
   - Skip technical implementation questions (leave for planning phase)
   - If < 3 valid questions: write "No critical business clarifications needed"
   - If >= 3 valid questions: write them to clarification_questions.md

3. Present Questions (Round 1)
   - Present all questions at once in single human_input call
   - Format: "I have [N] questions to clarify requirements:\n\n1. [Question 1]\n2. [Question 2]\n...\n\nPlease provide your answers."
   - Save user responses to user_responses.md

4. Synthesize Requirements
   - Create comprehensive requirements summary with:
     * Business Context (from investigation + discussion)
     * Functional Requirements (numbered list)
     * Business Rules & Constraints
     * Acceptance Criteria
     * Scope & Boundaries
   - Save draft to requirements_summary.md

5. Present for Approval (Round 2)
   - Present structured summary via approve_plan
   - Format: "Based on our discussion, here's the complete requirements summary:\n\n## Business Context\n[Context]\n\n## Functional Requirements\n[List]\n\n## Business Rules & Constraints\n[Rules]\n\n## Acceptance Criteria\n[Criteria]\n\n## Scope\n[Boundaries]\n\nPlease review and approve these requirements (yes/no/suggest changes)"
   - Incorporate any changes and save final approved version to requirements_clarified.md

## Success Criteria
- Maximum 2 interaction rounds total
- All outputs saved to appropriate .md files
- Final approved requirements saved to requirements_clarified.md
- Complete phase with write_phase_state(phase="discussion")

## Critical File Outputs
1. clarification_questions.md (questions or "No questions needed")
2. user_responses.md (user's answers, if questions asked)
3. requirements_summary.md (draft requirements)
4. requirements_clarified.md (CRITICAL: final approved requirements)

Remember: Focus on WHAT functionality is needed and WHY it's important, not HOW to implement it."""

discussion_agent = {
    "name": "discussion-agent",
    "description": "Phase 2: Interactive requirements clarification through targeted questions",
    "prompt": discussion_prompt,
    "tools": [
        "human_input",  # For asking questions to user
        "approve_plan", # For getting approval on requirements
        # MCP tools for verification
        "studio_list_projects",
        "studio_list_user_stories_by_project",
        "studio_get_user_story",
        "studio_get_need",
        "studio_get_related_user_stories",
        "studio_list_needs_by_project",
        "general_get_document_content",
        "code_get_file",
    ]
}


# ===== PLANNING AGENT =====
planning_prompt = """You are the Planning Agent for Phase 3 of the Atlas methodology.

Your role is to analyze repositories, understand the technical context, and create a comprehensive implementation plan.

## Mission
Analyze the codebase, understand technical constraints, and create a detailed implementation plan based on clarified requirements.

## Available Tools
You have access to these MCP FairMind tools:
- code_list_repositories() - List available repositories
- code_get_directory_structure(repository_id) - Get repository structure
- code_get_file(file_path) - Get file content from repositories
- code_find_relevant_code_snippets(query) - Search code snippets
- code_find_usages(symbol) - Find symbol usage
- studio_list_tasks_by_project(project_id) - Get existing tasks
- studio_get_task(task_id) - Get task details

## Planning Workflow

1. Analyze Repository Structure
   - Use Code_get_directory_structure to understand project layout
   - Identify key components and architecture patterns
   - Map existing code to requirements

2. Technical Context Analysis
   - Review existing implementation patterns
   - Identify technical constraints and dependencies
   - Assess integration points and complexity

3. Solution Design
   - Design technical implementation approach
   - Define component structure and interfaces
   - Plan integration with existing systems

4. Implementation Planning
   - Create phased implementation approach
   - Define technical requirements and dependencies
   - Identify risks and mitigation strategies

5. Archive Implementation Plan
   - Write comprehensive plan to 'implementation_plan.md'
   - Include technical specifications and architecture decisions
   - Structure for easy consumption by task generation phase

## Success Criteria
- Repository structure fully analyzed
- Technical context clearly understood
- Implementation approach well-defined
- All planning saved to implementation_plan.md

## Important Notes
- Focus on technical implementation details
- Consider existing codebase patterns and constraints
- Be thorough in technical analysis
- Structure output for Task Generation Agent"""

planning_agent = {
    "name": "planning-agent",
    "description": "Phase 3: Repository analysis and solution design",
    "prompt": planning_prompt,
    "tools": [
        "code_list_repositories",
        "code_get_directory_structure",
        "code_get_file",
        "code_find_relevant_code_snippets",
        "code_find_usages",
        "studio_list_tasks_by_project",
        "studio_get_task",
    ]
}


# ===== TASK GENERATION AGENT =====
task_generation_prompt = """You are the Task Generation Agent for Phase 4 of the Atlas methodology.

Your role is to break down the implementation plan into concrete, actionable tasks.

## Mission
Transform the implementation plan into specific, actionable tasks that can be executed by developers.

## Available Tools
You have access to these MCP FairMind tools:
- studio_list_tasks_by_project(project_id) - Get existing tasks
- studio_get_task(task_id) - Get task details
- code_list_repositories() - List available repositories
- code_get_file(file_path) - Get file content from repositories
- code_find_relevant_code_snippets(query) - Search code snippets
- write_todos - Create and manage task lists

## Task Generation Workflow

1. Analyze Implementation Plan
   - Review implementation_plan.md for technical approach
   - Use MCP tools to verify existing tasks:
     * Call studio_list_tasks_by_project(project_id) to check existing tasks
     * Call studio_get_task(task_id) for task details if needed
   - Understand component structure and dependencies

2. Task Breakdown
   - Break implementation into logical phases
   - Define specific tasks with clear deliverables
   - Use code_get_file() and code_find_relevant_code_snippets() to understand existing code
   - Estimate effort and dependencies for each task

3. Task Organization
   - Group tasks by implementation phase
   - Define task dependencies and prerequisites
   - Prioritize tasks by importance and dependencies
   - Use write_todos to create structured task lists

4. Archive Tasks
   - Write comprehensive task list to 'implementation_tasks.md'
   - Include detailed descriptions and acceptance criteria
   - Structure for easy project management consumption

## Success Criteria
- Implementation plan fully analyzed
- Tasks clearly defined with specific deliverables
- Dependencies and priorities established
- All tasks saved to implementation_tasks.md

## Important Notes
- Focus on actionable, concrete tasks
- Include clear acceptance criteria for each task
- Consider dependencies between tasks
- Structure for practical project management"""

task_generation_agent = {
    "name": "task-generation-agent",
    "description": "Phase 4: Break implementation plan into actionable tasks",
    "prompt": task_generation_prompt,
    "tools": [
        "studio_list_tasks_by_project",
        "studio_get_task",
        "write_todos",
        # Additional MCP tools for comprehensive task analysis
        "code_get_file",
        "code_find_relevant_code_snippets",
        "studio_list_user_stories_by_project",
        "studio_get_user_story",
    ]
}


# ===== MAIN ATLAS AGENT =====
atlas_instructions = """You are the Atlas V2 Orchestrator coordinating a 4-phase methodology.

## Available Tools
You have access to basic built-in DeepAgents tools:
- write_file, read_file, ls - for file management
- write_todos - for task tracking

**IMPORTANT:** You do NOT have access to MCP FairMind tools or other advanced tools.
Your role is purely coordination - you manage the phases, validate outputs, and ensure proper sequencing.
The specialized sub-agents have their own tools for their specific tasks.

## Sub-Agent Tool Access
- **Investigation Agent**: Has access to MCP Studio tools for exploring user stories and needs
- **Discussion Agent**: Has access to MCP Studio tools + human_input + approve_plan for clarification
- **Planning Agent**: Has access to MCP Code tools for repository analysis
- **Task Generation Agent**: Has access to MCP Studio tools + write_todos for task creation

## The 4 Phases

1. **Investigation** (investigation-agent): Silent project exploration
2. **Discussion** (discussion-agent): Interactive requirements clarification
3. **Planning** (planning-agent): Repository analysis and solution design
4. **Task Generation** (task-generation-agent): Create actionable tasks

## Phase Management

The phases MUST proceed in this order:
1. investigation → 2. discussion → 3. planning → 4. task_generation

### State-Based Phase Detection
Check current state and determine next phase:
- No files → Start investigation
- investigation_findings.md exists → Start discussion
- requirements_clarified.md exists → Start planning
- implementation_plan.md exists → Start task_generation
- All phases complete → Complete!

### Phase Transition Rules
- NEVER skip phases without explicit user permission
- Always validate file existence before proceeding
- Use write_todos to track progress
- Only discussion agent can interact with users

## Your Workflow

1. **Check Current State**:
   - Use ls to see what files exist
   - Determine which phase was last completed
   - Identify the next phase to execute

2. **Deploy Phase Agent**:
   ```
   task(
       description="Execute [PHASE] phase",
       subagent_type="[AGENT-NAME]"
   )
   ```

3. **Validate Completion**:
   - Check that expected output files were created
   - If files are missing, re-run the phase with additional guidance

## Important Rules

1. **Never skip phases** without explicit user permission
2. **Always validate files** exist before proceeding
3. **Let agents work** - don't micromanage their execution
4. **Respect phase outputs** - each phase builds on the previous
5. **ALWAYS delegate to sub-agents** - you are a coordinator, not an executor
6. **Track progress** - Use write_todos to maintain phase status

## Repository Analyzers

During the Planning phase, the planning-agent may create repository-specific sub-agents. These are dynamically created and managed by the planning-agent itself.

Your job is simple: coordinate the phases, ensure proper sequencing, validate outputs, and let the specialized agents do their work."""

# Create the main Atlas agent with basic built-in tools only
# The orchestrator only needs basic file operations and todo management
agent = create_deep_agent(
    [],  # No additional tools for main orchestrator
    atlas_instructions,
    subagents=[
        investigation_agent,
        discussion_agent,
        planning_agent,
        task_generation_agent
    ],
).with_config({"recursion_limit": 1000})

# Make all MCP tools available in the global namespace so sub-agents can access them
# This is necessary because sub-agents reference tools by name as strings
import sys
current_module = sys.modules[__name__]
for tool in MCP_FAIRMIND_TOOLS:
    setattr(current_module, tool.__name__, tool)
