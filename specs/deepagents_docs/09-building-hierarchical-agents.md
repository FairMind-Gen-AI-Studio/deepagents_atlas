# Building Hierarchical Agents

## Overview

Hierarchical agents are a powerful AI design paradigm where complex tasks are broken down and distributed among specialized sub-agents. This approach mirrors human organizational structures, with a high-level manager delegating responsibilities to domain specialists.

## Key Advantages of Hierarchical Agents

1. **Specialization**: Sub-agents focus on specific domains or capabilities
2. **Complexity Management**: Breaking complex tasks into manageable components
3. **Parallel Processing**: Multiple sub-agents can work simultaneously
4. **Improved Reasoning**: Different reasoning patterns applied to sub-tasks

## Core Components

### SubAgent Type Definition

```python
class SubAgent(TypedDict):
 name: str # Unique identifier for the sub-agent
 description: str # Description used by main agent to decide when to use this sub-agent
 prompt: str # System prompt that defines the sub-agent's behavior
 tools: NotRequired[list[str]] # Optional list of tool names this sub-agent can access
```

### Creating a Hierarchical Agent System

#### Step 1: Define Sub-Agents

Example of defining research and writing sub-agents:

```python
research_sub_agent = {
 "name": "research-agent",
 "description": "Used to research in-depth questions on specific topics.",
 "prompt": "You are a dedicated researcher. Your job is to conduct thorough research based on the user's questions."
}

writer_sub_agent = {
 "name": "writer-agent",
 "description": "Used to draft well-structured content based on research findings.",
 "prompt": "You are a professional writer. Your job is to create well-structured, clear content."
}
```

#### Step 2: Define Main Agent Instructions

Create clear instructions for the coordinator agent:

```python
main_agent_instructions = """You are a coordinator agent responsible for complex document analysis.

Use the research-agent to investigate specific questions about the document content.
Use the writer-agent to draft summaries and analysis based on the research findings.

Follow these steps:
1. Break down the user's request into specific research questions
2. Use the research-agent to investigate each question
3. Collect and synthesize the research findings
4. Use the writer-agent to create the final output"""
```

#### Step 3: Initialize the Hierarchical System

```python
from deepagents import create_deep_agent

# Define sub-agents
sub_agents = [research_sub_agent, writer_sub_agent]

# Create the hierarchical agent
agent = create_deep_agent(
    instructions=main_agent_instructions,
    sub_agents=sub_agents,
    tools=["tavily_search", "write_file"]  # Main agent tools
)
```

## Best Practices

### 1. Clear Role Definition
Each sub-agent should have a clearly defined role and responsibility:

```python
code_reviewer = {
    "name": "code-reviewer",
    "description": "Reviews code for quality, security, and best practices",
    "prompt": "You are an expert code reviewer. Analyze code for bugs, security issues, and adherence to best practices."
}
```

### 2. Proper Task Decomposition
Break complex tasks into logical sub-tasks:

```python
coordinator_prompt = """
When analyzing a software project:
1. Use the file-analyzer to understand the codebase structure
2. Use the code-reviewer to evaluate code quality
3. Use the security-auditor to identify potential vulnerabilities
4. Use the documentation-writer to create comprehensive reports
"""
```

### 3. Effective Communication Patterns
Establish clear communication protocols between agents:

```python
communication_prompt = """
When delegating to sub-agents:
- Provide clear, specific instructions
- Include relevant context and constraints
- Specify expected output format
- Set clear success criteria
"""
```

### 4. State Management
Use shared state effectively to maintain context across sub-agents:

```python
# Sub-agents inherit the main agent's state
# Use virtual filesystem for sharing data between agents
file_sharing_example = {
    "name": "data-processor",
    "description": "Processes and transforms data files",
    "prompt": "Process data and save results to virtual filesystem for other agents to use"
}
```

## Advanced Patterns

### Recursive Hierarchies
Sub-agents can have their own sub-agents for complex scenarios:

```python
analysis_coordinator = {
    "name": "analysis-coordinator", 
    "description": "Coordinates complex analysis tasks",
    "sub_agents": [data_cleaner, statistical_analyzer, visualizer]
}
```

### Conditional Agent Selection
Use dynamic agent selection based on task requirements:

```python
dynamic_selection_prompt = """
Choose the appropriate sub-agent based on the user's request:
- For data analysis: use data-analyst
- For code review: use code-reviewer  
- For documentation: use technical-writer
"""
```

### Parallel Execution
Design sub-agents to work in parallel when possible:

```python
parallel_research = {
    "name": "parallel-researcher",
    "description": "Conducts parallel research on multiple topics",
    "prompt": "Research your assigned topic independently and save findings to shared workspace"
}
```

## Implementation Considerations

### Performance Optimization
- Design sub-agents to work independently when possible
- Use caching for commonly accessed information
- Implement proper error handling and fallback mechanisms

### Context Management  
- Share relevant context between agents via virtual filesystem
- Implement context summarization for large datasets
- Use state archiving for long-running processes

### Tool Access Control
- Restrict tool access based on agent responsibilities
- Implement security boundaries between sub-agents
- Use tool validation to prevent misuse

## Example: Research and Analysis Pipeline

```python
# Define specialized agents
researcher = {
    "name": "researcher",
    "description": "Conducts in-depth research on specific topics",
    "prompt": "You are a thorough researcher. Investigate topics comprehensively.",
    "tools": ["tavily_search", "web_scraper"]
}

analyzer = {
    "name": "analyzer", 
    "description": "Analyzes research data and identifies patterns",
    "prompt": "You are a data analyst. Identify trends and insights from research data.",
    "tools": ["data_analysis", "statistical_tools"]
}

report_writer = {
    "name": "report-writer",
    "description": "Creates comprehensive reports from analysis",
    "prompt": "You are a technical writer. Create clear, structured reports.",
    "tools": ["document_generator", "chart_creator"]
}

# Create hierarchical agent
research_pipeline = create_deep_agent(
    instructions="Coordinate a complete research and analysis pipeline",
    sub_agents=[researcher, analyzer, report_writer],
    tools=["write_todos", "file_operations"]
)
```

This hierarchical approach enables sophisticated AI systems that can handle complex, multi-faceted tasks while maintaining clarity and organization in their execution.