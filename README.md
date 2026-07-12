# PROXY6 MCP Server

MCP (Model Context Protocol) server for managing proxies via the [PROXY6.net](https://px6.net) API.

## Tools

| Tool | Description |
|------|-------------|
| `get_account` | Show balance, email, user ID |
| `list_proxies` | List all owned proxies with full details |
| `get_prices` | Show pricing by version and duration |
| `get_count` | Check available stock for a country |
| `get_countries` | List countries available for a proxy version |
| `buy_proxy` | Purchase proxies |
| `prolong_proxy` | Extend rental period |
| `delete_proxy` | Delete proxies by ID or comment |
| `check_proxy` | Check if a proxy is valid |
| `set_description` | Update technical comment |

## Quick Start

```bash
# Install
pip install git+https://github.com/AsmanovLev/proxy6_mcp.git

# Set your API key
export PROXY6_API_KEY="your-key-here"

# Run
proxy6-mcp
```

## Usage with Hermes

1. Clone + install:
```bash
pip install -e /path/to/proxy6_mcp
```

2. Add to `~/.hermes/config.yaml`:
```yaml
mcp_servers:
  proxy6:
    command: bash
    args: ['/path/to/proxy6-mcp.sh']
    enabled: true
```

3. Create wrapper script `/path/to/proxy6-mcp.sh`:
```bash
#!/bin/bash
export PROXY6_API_KEY="your-key-here"
exec python3 -m proxy6_mcp
```

4. Run `/reload_mcp` in Hermes.

## API

All requests go to `https://px6.link/api/{api_key}/{method}/`.  
Rate limit: 3 requests/second.  
Returns JSON with `status: "yes"` on success.

### Proxy versions

| Version | Type | Price (30д) |
|---------|------|-------------|
| 3 | IPv4 Shared | ~33 RUB |
| 4 | IPv4 | ~120 RUB |
| 5 | MTProto | ~90 RUB |
| 6 | IPv6 | ~20.66 RUB |

## License

MIT
