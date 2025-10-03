Patra MCP Server
=================

This MCP server exposes three tools that access the Knowledge Graph directly (no REST):

- list_modelcards(limit=1000): List model cards from Neo4j
- get_modelcard(mc_id: str): Retrieve a single model card by ID
- search_modelcards(q: str, limit=50): Full-text search for model cards

Setup
-----

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure Neo4j connection via environment variables (defaults in parentheses):

```bash
export NEO4J_URI=neo4j://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PWD=your_password
```

Run (stdio)
-----------

```bash
python server.py
```

Integrate with Claude Desktop (example)
--------------------------------------

Add to claude_desktop_config.json:

```json
{
  "mcpServers": {
    "patra-mcp": {
      "command": "/absolute/path/to/your/.venv/bin/python",
      "args": ["/absolute/path/to/patra-kg/mcp_server/server.py"],
      "env": {
        "PATRA_BASE_URL": "http://localhost:5002"
      }
    }
  }
}
```

Restart the client. You should see the MCP tools available.


