#!/usr/bin/env python3
"""
Example usage of the DocGen agent.

This script demonstrates how to use the DocGen agent to generate
documentation for a codebase using MCP FairMind tools.
"""

import asyncio
import logging
from docgen_agent import create_docgen_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def example_basic_usage():
    """Basic usage example - document entire project."""
    logger.info("Creating DocGen agent...")
    agent = create_docgen_agent()

    logger.info("Running documentation generation...")
    result = await agent.run(
        user_request="Generate complete developer documentation for this project",
        project_id="my_project_id"  # Replace with actual project ID
    )

    print("\n" + "="*60)
    print("DOCUMENTATION GENERATION COMPLETE")
    print("="*60)
    print(f"\nFinal Response:\n{result['final_response']}")
    print(f"\nFiles Created ({len(result['files'])}):")
    for filename in sorted(result['files'].keys()):
        print(f"  - {filename}")
    print(f"\nTodos: {len(result['todos'])}")


async def example_targeted_documentation():
    """Example of documenting specific modules."""
    logger.info("Creating DocGen agent...")
    agent = create_docgen_agent()

    logger.info("Running targeted documentation generation...")
    result = await agent.run(
        user_request="""
        I need API reference documentation for the following modules:
        - Authentication module
        - User management module
        - Payment processing module

        Please include:
        - API reference with all public functions
        - Usage examples
        - Error handling guide

        Target audience: External developers integrating with our API
        """,
        project_id="my_project_id"
    )

    print("\n" + "="*60)
    print("TARGETED DOCUMENTATION COMPLETE")
    print("="*60)
    print(f"\nFinal Response:\n{result['final_response']}")


async def example_architecture_docs():
    """Example of generating architecture documentation."""
    logger.info("Creating DocGen agent...")
    agent = create_docgen_agent()

    logger.info("Running architecture documentation generation...")
    result = await agent.run(
        user_request="""
        Create architecture documentation for the entire system including:
        - System architecture overview with diagrams
        - Component interaction patterns
        - Data flow documentation
        - Technology stack details
        - Design decisions and rationale

        Target audience: New team members and system architects
        """,
        project_id="my_project_id"
    )

    print("\n" + "="*60)
    print("ARCHITECTURE DOCUMENTATION COMPLETE")
    print("="*60)
    print(f"\nFinal Response:\n{result['final_response']}")


async def main():
    """Run example scenarios."""
    print("DocGen Agent - Example Usage\n")
    print("Choose an example:")
    print("1. Basic usage - Complete documentation")
    print("2. Targeted documentation - Specific modules")
    print("3. Architecture documentation")
    print("4. Run all examples")

    choice = input("\nEnter choice (1-4): ").strip()

    try:
        if choice == "1":
            await example_basic_usage()
        elif choice == "2":
            await example_targeted_documentation()
        elif choice == "3":
            await example_architecture_docs()
        elif choice == "4":
            logger.info("Running all examples...")
            await example_basic_usage()
            await example_targeted_documentation()
            await example_architecture_docs()
        else:
            print("Invalid choice!")
            return
    except Exception as e:
        logger.error(f"Error running example: {e}", exc_info=True)
        return

    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
