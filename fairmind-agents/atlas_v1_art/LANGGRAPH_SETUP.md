# LangGraph Setup for Atlas V1 ART

## Quick Start

Run Atlas V1 with ART in LangGraph Studio:

```bash
langgraph dev
```

If you encounter blocking I/O errors, use:

```bash
langgraph dev --allow-blocking
```

## Configuration Status

### ✅ Fixed Issues

1. **MCP Import Issue**
   - Added `langchain-mcp-adapters` and `nest_asyncio` to pyproject.toml
   - Added current directory to Python path for module resolution

2. **OpenRouter Base URL Issue**
   - Fixed base_url to correctly use https://openrouter.ai/api/v1
   - No longer defaults to OpenAI's API endpoint

3. **Blocking I/O Issue (Partial Fix)**
   - Created async-safe wrapper for ART model
   - Prevents some blocking I/O errors

### ⚠️ Known Issues

1. **ART File I/O**
   - OpenPipe ART's logging uses synchronous file writes
   - May still cause blocking errors in some cases
   - Workaround: Use `--allow-blocking` flag

2. **MCP Authentication**
   - Current token returns 403 Forbidden
   - System works without MCP tools but with limited capabilities

## Environment Variables

Ensure your `.env` file contains:

```env
# OpenRouter Configuration
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=z-ai/glm-4.5

# MCP Configuration (optional)
FAIRMIND_MCP_URL=https://project-context.mindstream.fairmind.ai/mcp/mcp/
FAIRMIND_MCP_TOKEN=your_valid_token

# OpenPipe ART
ENABLE_OPENPIPE_ART=true
OPENPIPE_PROJECT=atlas-v1-art
```

## Testing the Setup

1. **Test MCP Import**:
   ```bash
   python verify_mcp_fix.py
   ```

2. **Test OpenRouter**:
   ```bash
   python test_openrouter_fix.py
   ```

3. **Test Complete System**:
   ```bash
   python test_final.py
   ```

## Troubleshooting

### Error: "Blocking call to io.TextIOWrapper.write"
**Solution**: Run with `langgraph dev --allow-blocking`

### Error: "MCP client module not available"
**Solution**: Ensure `langchain-mcp-adapters` is installed:
```bash
pip install langchain-mcp-adapters
```

### Error: "401 - Incorrect API key provided"
**Solution**: Check that OPENROUTER_API_KEY is set correctly, not being sent to OpenAI

### Error: "403 Forbidden" for MCP
**Solution**: Update FAIRMIND_MCP_TOKEN with a valid token

## Architecture Overview

```
Atlas V1 ART
├── graph.py                    # Main LangGraph entry point
├── reinforcement/
│   ├── model_wrapper.py        # ART model wrapping
│   ├── async_art_wrapper.py    # Async-safe wrapper
│   └── trajectory_storage.py   # Trajectory management
├── agents/                     # 4-phase agents
├── mcp_client.py               # MCP integration
└── langgraph.json              # LangGraph configuration
```

## Next Steps

1. Get a valid MCP token for full functionality
2. Consider implementing full async ART logging (upstream fix needed)
3. Test with production workloads

---

For more details, see the main README.md and MCP_FIX_SUMMARY.md