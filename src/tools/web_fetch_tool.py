import re

import httpx

from src.tool import Tool, ToolResult, build_tool
from src.utils.format import truncate

_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {
            "type": "string",
            "description": "The URL to fetch.",
        },
        "prompt": {
            "type": "string",
            "description": (
                "Optional: what you want to extract from the page."
            ),
        },
        "max_length": {
            "type": "integer",
            "description": "Max chars to return (default 50000).",
        },
        "start_index": {
            "type": "integer",
            "description": "Start reading from this char offset.",
        },
    },
    "required": ["url"],
}

_TIMEOUT = 30.0
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; Lilith/1.0; +https://github.com)"
    )
}


async def _call(args: dict, ctx) -> ToolResult:
    url = args["url"]
    max_length = int(args.get("max_length", 50_000))
    start_index = int(args.get("start_index", 0))

    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=_TIMEOUT
        ) as client:
            resp = await client.get(url, headers=_HEADERS)
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return ToolResult(
            content=[
                {
                    "type": "text",
                    "text": f"HTTP {exc.response.status_code}: {url}",
                }
            ],
            is_error=True,
        )
    except Exception as exc:
        return ToolResult(
            content=[{"type": "text", "text": str(exc)}],
            is_error=True,
        )

    content_type = resp.headers.get("content-type", "")
    body = resp.text

    if "html" in content_type:
        body = _strip_html(body)

    body = body[start_index : start_index + max_length]
    body = truncate(body, max_length)

    return ToolResult(content=[{"type": "text", "text": body}])


def _strip_html(html: str) -> str:
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"&nbsp;", " ", html)
    html = re.sub(r"&amp;", "&", html)
    html = re.sub(r"&lt;", "<", html)
    html = re.sub(r"&gt;", ">", html)
    html = re.sub(r"[ \t]+", " ", html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()


TOOL = build_tool(
    Tool(
        name="WebFetch",
        description=(
            "Fetch a URL and return its text content. "
            "HTML is stripped to plain text. "
            "Use start_index to paginate through large pages."
        ),
        input_schema=_SCHEMA,
        call=_call,
        is_read_only=lambda _: True,
        search_hint="fetch url http web page download content",
    )
)
