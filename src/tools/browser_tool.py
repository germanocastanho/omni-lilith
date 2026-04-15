from __future__ import annotations

import base64
import json
from typing import Any

from src.tool import Tool, ToolResult, build_tool

_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "open", "click", "type", "read", "html",
                "run", "screenshot", "scroll", "select",
                "wait", "back", "forward", "close",
            ],
            "description": (
                "Browser action to perform:\n"
                "- open: navigate to URL (required: url)\n"
                "- click: click a CSS selector (required: selector)\n"
                "- type: type text into selector (required: selector, text)\n"
                "- read: get visible text (optional: selector; defaults to full page)\n"
                "- html: get raw HTML (optional: selector)\n"
                "- run: execute JavaScript (required: script)\n"
                "- screenshot: capture page as base64 PNG\n"
                "- scroll: scroll by pixels (optional: x, y; defaults 0, 500)\n"
                "- select: select <option> by value (required: selector, value)\n"
                "- wait: wait for selector to appear (required: selector)\n"
                "- back: navigate back\n"
                "- forward: navigate forward\n"
                "- close: close browser session"
            ),
        },
        "url": {"type": "string", "description": "URL to navigate to (action: open)"},
        "selector": {"type": "string", "description": "CSS selector"},
        "text": {"type": "string", "description": "Text to type"},
        "script": {"type": "string", "description": "JavaScript to execute"},
        "value": {"type": "string", "description": "Option value to select"},
        "x": {"type": "integer", "description": "Horizontal scroll pixels (default 0)"},
        "y": {"type": "integer", "description": "Vertical scroll pixels (default 500)"},
        "timeout": {
            "type": "integer",
            "description": "Timeout in ms for wait actions (default 10000)",
        },
    },
    "required": ["action"],
}

# Module-level browser state — one session per process.
_state: dict[str, Any] = {
    "playwright": None,
    "browser": None,
    "page": None,
}


async def _ensure_browser() -> Any:
    from playwright.async_api import async_playwright

    if _state["playwright"] is None:
        pw = await async_playwright().__aenter__()
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        _state["playwright"] = pw
        _state["browser"] = browser
        _state["page"] = page
    return _state["page"]


async def _call(args: dict, ctx) -> ToolResult:
    action = args["action"]

    if action == "close":
        if _state["browser"]:
            await _state["browser"].close()
            await _state["playwright"].__aexit__(None, None, None)
            _state.update({"playwright": None, "browser": None, "page": None})
        return ToolResult(content=[{"type": "text", "text": "Browser closed."}])

    page = await _ensure_browser()

    try:
        if action == "open":
            url = args.get("url", "")
            await page.goto(url, wait_until="domcontentloaded")
            title = await page.title()
            return ToolResult(content=[{"type": "text", "text": f"Navigated to: {url}\nTitle: {title}"}])

        elif action == "click":
            selector = args["selector"]
            await page.click(selector)
            return ToolResult(content=[{"type": "text", "text": f"Clicked: {selector}"}])

        elif action == "type":
            selector = args["selector"]
            text = args.get("text", "")
            await page.fill(selector, text)
            return ToolResult(content=[{"type": "text", "text": f"Typed into {selector}"}])

        elif action == "read":
            selector = args.get("selector")
            if selector:
                el = page.locator(selector)
                text = await el.inner_text()
            else:
                text = await page.inner_text("body")
            return ToolResult(content=[{"type": "text", "text": text}])

        elif action == "html":
            selector = args.get("selector")
            if selector:
                el = page.locator(selector)
                html = await el.inner_html()
            else:
                html = await page.content()
            return ToolResult(content=[{"type": "text", "text": html}])

        elif action == "run":
            script = args["script"]
            result = await page.evaluate(script)
            return ToolResult(content=[{"type": "text", "text": json.dumps(result, ensure_ascii=False)}])

        elif action == "screenshot":
            data = await page.screenshot(full_page=False)
            b64 = base64.b64encode(data).decode()
            return ToolResult(content=[{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}}])

        elif action == "scroll":
            x = args.get("x", 0)
            y = args.get("y", 500)
            await page.evaluate(f"window.scrollBy({x}, {y})")
            return ToolResult(content=[{"type": "text", "text": f"Scrolled by ({x}, {y})"}])

        elif action == "select":
            selector = args["selector"]
            value = args["value"]
            await page.select_option(selector, value=value)
            return ToolResult(content=[{"type": "text", "text": f"Selected '{value}' in {selector}"}])

        elif action == "wait":
            selector = args["selector"]
            timeout = args.get("timeout", 10000)
            await page.wait_for_selector(selector, timeout=timeout)
            return ToolResult(content=[{"type": "text", "text": f"Selector appeared: {selector}"}])

        elif action == "back":
            await page.go_back()
            return ToolResult(content=[{"type": "text", "text": f"Back → {page.url}"}])

        elif action == "forward":
            await page.go_forward()
            return ToolResult(content=[{"type": "text", "text": f"Forward → {page.url}"}])

        else:
            return ToolResult(
                content=[{"type": "text", "text": f"Unknown action: {action}"}],
                is_error=True,
            )

    except Exception as exc:
        return ToolResult(
            content=[{"type": "text", "text": f"Browser error: {exc}"}],
            is_error=True,
        )


TOOL = build_tool(
    Tool(
        name="Browser",
        description=(
            "Control a real Chromium browser. Navigate pages, click elements, "
            "fill forms, extract text/HTML, run JavaScript, take screenshots. "
            "State persists across calls within a session."
        ),
        input_schema=_SCHEMA,
        call=_call,
        search_hint="browser web navigate click scrape playwright chromium",
    )
)
