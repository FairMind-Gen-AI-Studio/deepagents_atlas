#!/bin/bash

##############################################################################
# LangGraph Checkpoint Cleanup & Fresh Start
#
# This script clears all LangGraph checkpoint files and restarts the server
# in a clean state. Useful when you want to discard accumulated checkpoint
# state (previous executions, interrupted runs, etc.)
#
# Usage: ./scripts/clean_start.sh
##############################################################################

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🧹 LangGraph Checkpoint Cleanup"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Kill any running langgraph processes
echo "🛑 Stopping any running LangGraph servers..."
if pgrep -f "langgraph dev" > /dev/null; then
    pkill -f "langgraph dev" || true
    echo "   ✅ Stopped"
    sleep 1
else
    echo "   ℹ️  No running server found"
fi

echo ""
echo "🗑️  Removing checkpoint files and logs..."

# Step 2: Remove server.log if it exists
if [ -f "server.log" ]; then
    echo "   🔥 server.log"
    rm -f server.log
fi

# Step 3: Find and remove all .langgraph_api directories
CHECKPOINT_DIRS=(
    ".langgraph_api"
    "fairmind-agents/atlas_v1/.langgraph_api"
    "fairmind-agents/docgen/.langgraph_api"
    "fairmind-agents/archqa/.langgraph_api"
    "fairmind-agents/research/.langgraph_api"
)

TOTAL_REMOVED=0
for dir in "${CHECKPOINT_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        FILES_COUNT=$(find "$dir" -name "*.pckl" 2>/dev/null | wc -l)
        if [ "$FILES_COUNT" -gt 0 ]; then
            echo "   🔥 $dir ($FILES_COUNT files)"
            rm -rf "$dir"
            ((TOTAL_REMOVED += FILES_COUNT))
        fi
    fi
done

# Step 4: Remove any orphaned .pckl files
ORPHANED=$(find . -name "*.pckl" -type f 2>/dev/null | grep -v node_modules | wc -l)
if [ "$ORPHANED" -gt 0 ]; then
    echo "   🔥 Removing $ORPHANED orphaned .pckl files"
    find . -name "*.pckl" -type f ! -path "*/node_modules/*" -delete
    ((TOTAL_REMOVED += ORPHANED))
fi

echo ""
if [ "$TOTAL_REMOVED" -gt 0 ]; then
    echo -e "${GREEN}✅ Cleanup complete! ($TOTAL_REMOVED checkpoint files removed)${NC}"
else
    echo -e "${YELLOW}ℹ️  No checkpoint files found${NC}"
fi

echo ""
echo "🚀 Starting fresh LangGraph server..."
echo "   URL: http://127.0.0.1:2024"
echo "   Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Step 5: Start fresh
langgraph dev --no-browser 2>&1 | tee server.log
