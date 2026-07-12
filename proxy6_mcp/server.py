"""MCP server for PROXY6.net API.

Provides tools to manage proxy rentals: list, buy, prolong, delete, check.

Requires PROXY6_API_KEY environment variable.
"""
import os
import json
import httpx
from mcp.server.fastmcp import FastMCP

API_KEY = os.environ.get("PROXY6_API_KEY", "")
BASE_URL = f"https://px6.link/api/{API_KEY}"

mcp = FastMCP("proxy6")

VERSION_NAMES = {"3": "IPv4 Shared", "4": "IPv4", "5": "MTProto", "6": "IPv6"}


def _api(path: str, params: dict | None = None) -> dict:
    """Make a GET request to the PROXY6 API."""
    url = f"{BASE_URL}/{path}/" if path else BASE_URL
    resp = httpx.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _fmt_proxy(p: dict) -> str:
    """Format a single proxy entry."""
    ver = VERSION_NAMES.get(p.get("version", ""), p.get("version", "?"))
    return (
        f"ID:{p.get('id', '?')} [{ver}] "
        f"{p['host']}:{p['port']} "
        f"login:{p.get('user', '?')} pass:{p.get('pass', '?')} "
        f"country:{p.get('country', '?').upper()} "
        f"type:{p.get('type', '?')} "
        f"expires:{p.get('date_end', '?')} "
        f"{'✅' if p.get('active') == '1' else '❌'}"
    )


# ── Tools ──────────────────────────────────────────────────────────────


@mcp.tool(description="Show account info: balance, email, user ID.")
async def get_account() -> str:
    """Get the current account details (balance, referral balance, email)."""
    data = _api("")
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool(description="Show referral balance and partnership stats.")
async def get_referral_info() -> str:
    """Get referral/partnership balance from the account.
    
    Note: referral payout and link management are only available via the website
    (https://px6.net/partnership). The API only exposes the balance_ref field.
    """
    data = _api("")
    cur = data.get("currency", "RUB")
    return (
        f"Referral balance: {data.get('balance_ref', '?')} {cur}\n"
        f"Main balance: {data['balance']} {cur}\n"
        f"\n📌 Partnership terms (from px6.net):\n"
        f"  • 30% commission on first payment, 20% on subsequent\n"
        f"  • Referral user is assigned for life\n"
        f"  • Bonus can be used for services or withdrawn\n"
        f"  • Withdrawal: USDT (ERC20/BEP20), WebMoney WMZ\n"
        f"\n🔗 Manage: https://px6.net/partnership"
    )


@mcp.tool(description="List all owned proxies with full details.")
async def list_proxies() -> str:
    """Fetch and display all rented proxies."""
    data = _api("getproxy")
    if data.get("status") != "yes":
        return json.dumps(data, ensure_ascii=False, indent=2)

    proxies = data.get("list", {})
    if not proxies:
        return "No proxies found."

    lines = [f"Total: {data.get('list_count', 0)} proxies\n"]
    for pid, p in sorted(proxies.items(), key=lambda x: int(x[0])):
        lines.append(_fmt_proxy(p))
    return "\n".join(lines)


@mcp.tool(description="Show pricing table for all proxy versions.")
async def get_prices() -> str:
    """Display the current price list per version and duration."""
    data = _api("getprice")
    if data.get("status") != "yes":
        return json.dumps(data, ensure_ascii=False, indent=2)

    cur = data.get("currency", "RUB")
    lines = [f"Balance: {data['balance']} {cur}\n"]
    for ver, prices in sorted(data.get("data", {}).items()):
        name = VERSION_NAMES.get(ver, f"v{ver}")
        lines.append(f"\n{name}:")
        for days, price in sorted(prices.items(), key=lambda x: int(x[0])):
            lines.append(f"  {days}д = {price} {cur}")
    return "\n".join(lines)


@mcp.tool(
    description="Check how many proxies are available for purchase in a country."
)
async def get_count(country: str, version: str = "6") -> str:
    """Query available stock for a country + version.

    Args:
        country: Country code in ISO2 format (e.g. ru, us, nl).
        version: Proxy version: 3=IPv4 Shared, 4=IPv4, 5=MTProto, 6=IPv6. Defaults to 6.
    """
    data = _api("getcount", {"country": country, "version": version})
    if data.get("status") != "yes":
        return json.dumps(data, ensure_ascii=False, indent=2)
    return f"Available v{version} in {country.upper()}: {data['count']} pcs"


@mcp.tool(
    description="List available countries for a proxy version."
)
async def get_countries(version: str = "4") -> str:
    """Get the list of countries where proxies are available.

    Args:
        version: Proxy version: 3=IPv4 Shared, 4=IPv4, 5=MTProto, 6=IPv6. Defaults to 4.
    """
    data = _api("getcountry", {"version": version})
    if data.get("status") != "yes":
        return json.dumps(data, ensure_ascii=False, indent=2)
    countries = data.get("list", [])
    name = VERSION_NAMES.get(version, f"v{version}")
    return f"Available countries for {name} ({len(countries)}):\n" + ", ".join(
        c.upper() for c in countries
    )


@mcp.tool(description="Purchase proxies (IPv6 by default).")
async def buy_proxy(
    country: str,
    count: int = 1,
    period: int = 30,
    version: str = "6",
    descr: str = "",
) -> str:
    """Buy proxies from the available stock.

    Args:
        country: Country code in ISO2 format (e.g. ru, us, nl).
        count: Number of proxies to buy (default: 1).
        period: Rental period in days (default: 30).
        version: Proxy version: 3=IPv4 Shared, 4=IPv4, 5=MTProto, 6=IPv6 (default: 6).
        descr: Optional technical comment (max 50 chars).
    """
    params = {
        "country": country,
        "count": count,
        "period": period,
        "version": version,
    }
    if descr:
        params["descr"] = descr[:50]

    data = _api("buy", params)
    if data.get("status") != "yes":
        return json.dumps(data, ensure_ascii=False, indent=2)

    proxies = data.get("list", {})
    lines = [
        f"Order #{data.get('order_id', '?')} — {count}x {country.upper()} "
        f"v{version} for {period}д",
        f"Price: {data.get('price', '?')} {data.get('currency', '')} | "
        f"Balance: {data.get('balance', '?')} {data.get('currency', '')}",
    ]
    for pid, p in sorted(proxies.items(), key=lambda x: int(x[0])):
        lines.append(f"\n{_fmt_proxy(p)}")
    return "\n".join(lines)


@mcp.tool(description="Extend proxy rental period.")
async def prolong_proxy(ids: str, period: int = 30) -> str:
    """Extend the rental period of existing proxies.

    Args:
        ids: Comma-separated proxy IDs (e.g. "40278065,40278074").
        period: Extension period in days (default: 30).
    """
    data = _api("prolong", {"ids": ids, "period": period})
    if data.get("status") != "yes":
        return json.dumps(data, ensure_ascii=False, indent=2)

    lines = [
        f"Extended {data.get('count', '?')} proxies for {period}д",
        f"Price: {data.get('price', '?')} {data.get('currency', '')} | "
        f"Balance: {data.get('balance', '?')} {data.get('currency', '')}",
    ]
    for pid, p in (data.get("list") or {}).items():
        lines.append(f"  ID:{p['id']} → expires {p['date_end']}")
    return "\n".join(lines)


@mcp.tool(description="Delete proxies by ID or technical comment.")
async def delete_proxy(ids: str = "", descr: str = "") -> str:
    """Remove proxies from your account.

    Args:
        ids: Comma-separated proxy IDs to delete (e.g. "40278065,40278074").
        descr: Alternative — delete all proxies with this technical comment.
    """
    params = {}
    if ids:
        params["ids"] = ids
    if descr:
        params["descr"] = descr
    if not params:
        return "Provide either ids or descr."

    data = _api("delete", params)
    if data.get("status") != "yes":
        return json.dumps(data, ensure_ascii=False, indent=2)
    return f"Deleted {data.get('count', 0)} proxy/proxies."


@mcp.tool(description="Check if a proxy is valid.")
async def check_proxy(ids: str = "", proxy: str = "") -> str:
    """Check proxy validity by internal ID or direct connection string.

    Args:
        ids: Internal proxy ID from your list.
        proxy: Direct proxy string in format ip:port:user:pass.
    """
    params = {}
    if ids:
        params["ids"] = ids
    if proxy:
        params["proxy"] = proxy
    if not params:
        return "Provide either ids or proxy."

    data = _api("check", params)
    if data.get("status") != "yes":
        return json.dumps(data, ensure_ascii=False, indent=2)

    status = data.get("proxy_status", False)
    label = ids or proxy
    return f"Proxy {label}: {'✅ VALID' if status else '❌ INVALID'}"


@mcp.tool(description="Update technical comment on proxies.")
async def set_description(old: str, new: str) -> str:
    """Change the technical comment (descr) on proxies matching a given comment.

    Args:
        old: Current comment text to search for.
        new: New comment text (max 50 chars).
    """
    data = _api("setdescr", {"old": old, "new": new[:50]})
    if data.get("status") != "yes":
        return json.dumps(data, ensure_ascii=False, indent=2)
    return f"Updated {data.get('count', 0)} proxies: '{old}' → '{new[:50]}'"


def main():
    """Entry point: run the MCP server on stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
