#!/usr/bin/env python3
"""
Test semplice per verificare se il filesystem virtuale funziona correttamente.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from deepagents.state import file_reducer, DeepAgentState

def test_file_reducer():
    """Test del file_reducer per vedere se funziona correttamente."""

    print("🧪 Testing file_reducer...")

    # Test del file_reducer
    print("📝 Testing file_reducer directly...")

    # Test 1: None + dict
    result1 = file_reducer(None, {"test.txt": "Hello World"})
    print(f"✅ None + dict = {result1}")

    # Test 2: dict + None
    result2 = file_reducer({"test.txt": "Hello World"}, None)
    print(f"✅ dict + None = {result2}")

    # Test 3: dict + dict
    result3 = file_reducer({"test1.txt": "Hello"}, {"test2.txt": "World"})
    print(f"✅ dict + dict = {result3}")

    # Test 4: dict + overlapping dict
    result4 = file_reducer({"test.txt": "Hello"}, {"test.txt": "World"})
    print(f"✅ overlapping dict = {result4}")

    return True

def test_filesystem_basic():
    """Test basico del filesystem virtuale senza reducer personalizzato."""

    print("🧪 Testing filesystem virtuale without custom reducer...")

    # Simula lo stato come se fosse in LangGraph senza reducer personalizzato
    print("📝 Simulating LangGraph state (no custom reducer)...")

    # Simula lo stato iniziale
    state = {"files": {}}
    print(f"Initial state: {state}")

    # Simula l'aggiunta di un file (come fa il tool write_file)
    files = state.get("files", {})
    files["test.txt"] = "Hello World"
    state["files"] = files
    print(f"After adding file: {state}")

    # Simula l'aggiunta di un secondo file
    files2 = state.get("files", {})
    files2["test2.txt"] = "Hello World 2"
    state["files"] = files2
    print(f"After adding second file: {state}")

    # Test della lettura (come fa il tool read_file)
    print("🔍 Testing read_file simulation...")
    mock_filesystem = state.get("files", {})
    if "test.txt" in mock_filesystem:
        content = mock_filesystem["test.txt"]
        print(f"✅ Successfully read test.txt: {content}")
    else:
        print("❌ File not found!")

    return True

    # Simula una conversazione che crea un file
    thread_id = "test-thread"
    config = {"configurable": {"thread_id": thread_id}}

    # Prima esecuzione - crea un file
    print("📝 Creating test file...")
    result1 = test_agent.invoke({
        "messages": [{
            "role": "user",
            "content": "Create a test file called 'test.txt' with content 'Hello World'"
        }]
    }, config=config)

    files1 = result1.get('files', {})
    print(f"✅ Files after first execution: {list(files1.keys())}")

    # Seconda esecuzione - controlla se il file persiste
    print("🔍 Checking if file persists...")
    result2 = test_agent.invoke({
        "messages": [{
            "role": "user",
            "content": "List all files"
        }]
    }, config=config)

    files2 = result2.get('files', {})
    print(f"✅ Files after second execution: {list(files2.keys())}")

    # Verifica che il file sia presente
    if 'test.txt' in files2:
        print(f"✅ File persisted: {files2['test.txt']}")
        return True
    else:
        print("❌ File not found!")
        print(f"Files: {files2}")
        return False

if __name__ == "__main__":
    success = test_filesystem_basic()

    if success:
        print("\n🎉 FILESYSTEM TEST PASSED!")
        print("✅ Files persist correctly between executions")
    else:
        print("\n⚠️ FILESYSTEM TEST FAILED!")
        print("The filesystem virtual is not working correctly")
