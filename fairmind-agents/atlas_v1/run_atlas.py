#!/usr/bin/env python
"""
Run Atlas V1 Agent directly with Python
"""

import asyncio
import sys
from atlas_agent import create_atlas_agent
import logging

# Optional: Enable debug logging
# logging.basicConfig(level=logging.DEBUG)

async def main():
    """Main execution function"""
    
    # Initialize the Atlas agent
    print("🚀 Initializing Atlas V1 Agent...")
    agent = create_atlas_agent()
    
    # Check agent status
    status = agent.get_status()
    print(f"✅ Agent initialized. Status: {status}")
    
    # Get user input for the task
    if len(sys.argv) > 1:
        # Use command line argument if provided
        user_request = " ".join(sys.argv[1:])
    else:
        # Interactive prompt
        print("\n📝 Enter your request (e.g., 'Analyze user story US-123'):")
        user_request = input("> ").strip()
        
        if not user_request:
            user_request = "Analyze the BlogMaster AI project and create a technical plan"
    
    # Optional: Specify project_id if known
    project_id = None  # Will auto-detect from MCP if not specified
    
    print(f"\n🔍 Processing request: {user_request}")
    print("=" * 60)
    
    try:
        # Run the agent
        result = await agent.run(
            user_request,
            project_id=project_id
        )
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 Results:")
        print("=" * 60)
        
        if "final_response" in result:
            print(result["final_response"])
        else:
            print("No final response generated")
            
        # List generated files
        files = agent.list_virtual_files()
        if files:
            print("\n📁 Generated files in virtual filesystem:")
            for file in files:
                print(f"  - {file}")
                
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())