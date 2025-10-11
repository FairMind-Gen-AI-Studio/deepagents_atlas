#!/usr/bin/env python3
"""
Test per verificare se LangGraph API gestisce correttamente gli aggiornamenti al campo files.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage, BaseMessage
from typing import Annotated, Dict, Any, List
from langgraph.prebuilt import InjectedState

def test_langgraph_files():
    """Test se LangGraph gestisce correttamente gli aggiornamenti al campo files."""

    print("🧪 Testing LangGraph files handling...")

    # Crea uno state schema compatibile con LangGraph API
    # Per semplicità, usiamo un dict con i tipi appropriati
    from typing import Any
    TestState = dict  # Temporaneamente usa dict per evitare problemi di tipo

    @tool
    def test_write_file(file_path: str, content: str, state: Annotated[TestState, InjectedState]) -> Command:
        """Test tool che simula write_file."""
        files = state.get("files", {})
        files[file_path] = content
        print(f"📝 Tool executed: Added {file_path} with content: {content[:50]}...")
        return Command(
            update={
                "files": files,
                "messages": [ToolMessage(f"Updated file {file_path}")]
            }
        )

    @tool
    def test_read_file(file_path: str, state: Annotated[TestState, InjectedState]) -> str:
        """Test tool che simula read_file."""
        files = state.get("files", {})
        if file_path in files:
            return files[file_path]
        else:
            return f"File '{file_path}' not found"

    # Crea un agente di test
    test_agent = create_react_agent(
        model=None,  # Non serve un modello per questo test
        tools=[test_write_file, test_read_file],
        system_prompt="Test agent for file handling",
        state_schema=TestState  # State schema compatibile con LangGraph API
    )

    # Simula una conversazione
    thread_id = "test-thread"
    config = {"configurable": {"thread_id": thread_id}}

    # Prima esecuzione - crea un file
    print("📝 First execution - creating file...")
    result1 = test_agent.invoke({
        "messages": [{
            "role": "user",
            "content": "Create a test file called 'test.txt' with content 'Hello World'"
        }]
    }, config=config)

    files1 = result1.get('files', {})
    print(f"✅ Files after first execution: {list(files1.keys())}")

    if 'test.txt' in files1:
        print(f"✅ File created: {files1['test.txt']}")
    else:
        print("❌ File not created!")
        return False

    # Seconda esecuzione - controlla se il file persiste
    print("🔍 Second execution - checking persistence...")
    result2 = test_agent.invoke({
        "messages": [{
            "role": "user",
            "content": "Read the file 'test.txt'"
        }]
    }, config=config)

    files2 = result2.get('files', {})
    print(f"✅ Files after second execution: {list(files2.keys())}")

    if 'test.txt' in files2:
        print(f"✅ File persisted: {files2['test.txt']}")
        return True
    else:
        print("❌ File not found!")
        print(f"Files: {files2}")
        return False

if __name__ == "__main__":
    success = test_langgraph_files()

    if success:
        print("\n🎉 LANGGRAPH FILES TEST PASSED!")
        print("✅ LangGraph handles file updates correctly")
    else:
        print("\n⚠️ LANGGRAPH FILES TEST FAILED!")
        print("LangGraph is not handling file updates correctly")
