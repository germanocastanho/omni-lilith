from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.tools.browser_tool as browser_mod
from src.tools.browser_tool import _call


def _reset_state():
    browser_mod._state.update({"playwright": None, "browser": None, "page": None})


def _mock_page():
    page = AsyncMock()
    page.title = AsyncMock(return_value="Test Page")
    page.url = "https://example.com"
    page.inner_text = AsyncMock(return_value="page text")
    page.inner_html = AsyncMock(return_value="<p>html</p>")
    page.content = AsyncMock(return_value="<html></html>")
    page.evaluate = AsyncMock(return_value=42)
    page.screenshot = AsyncMock(return_value=b"PNG")
    locator = AsyncMock()
    locator.inner_text = AsyncMock(return_value="element text")
    locator.inner_html = AsyncMock(return_value="<span>ok</span>")
    page.locator = MagicMock(return_value=locator)
    return page


def _patch_browser(page):
    return patch.object(browser_mod, "_ensure_browser", new=AsyncMock(return_value=page))


@pytest.fixture(autouse=True)
def reset():
    _reset_state()
    yield
    _reset_state()


async def test_close_when_no_browser(ctx):
    result = await _call({"action": "close"}, ctx)
    assert "closed" in result.content[0]["text"].lower()


async def test_close_existing_browser(ctx):
    pw = AsyncMock()
    browser = AsyncMock()
    browser_mod._state.update({"playwright": pw, "browser": browser, "page": AsyncMock()})
    result = await _call({"action": "close"}, ctx)
    browser.close.assert_awaited_once()
    assert "closed" in result.content[0]["text"].lower()


async def test_open_url(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "open", "url": "https://example.com"}, ctx)
    assert "example.com" in result.content[0]["text"]
    assert "Test Page" in result.content[0]["text"]


async def test_click(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "click", "selector": "#btn"}, ctx)
    assert "#btn" in result.content[0]["text"]
    page.click.assert_awaited_once_with("#btn")


async def test_type(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "type", "selector": "input", "text": "hello"}, ctx)
    page.fill.assert_awaited_once_with("input", "hello")
    assert "input" in result.content[0]["text"]


async def test_read_full_page(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "read"}, ctx)
    assert result.content[0]["text"] == "page text"


async def test_read_with_selector(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "read", "selector": ".content"}, ctx)
    assert result.content[0]["text"] == "element text"


async def test_html_full_page(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "html"}, ctx)
    assert "<html>" in result.content[0]["text"]


async def test_run_script(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "run", "script": "return 42"}, ctx)
    assert "42" in result.content[0]["text"]


async def test_screenshot(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "screenshot"}, ctx)
    assert result.content[0]["type"] == "image"


async def test_scroll_defaults(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "scroll"}, ctx)
    page.evaluate.assert_awaited_once_with("window.scrollBy(0, 500)")
    assert "Scrolled" in result.content[0]["text"]


async def test_scroll_custom(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "scroll", "x": 100, "y": 200}, ctx)
    page.evaluate.assert_awaited_once_with("window.scrollBy(100, 200)")


async def test_select(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "select", "selector": "select#s", "value": "opt1"}, ctx)
    page.select_option.assert_awaited_once_with("select#s", value="opt1")
    assert "opt1" in result.content[0]["text"]


async def test_wait(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "wait", "selector": ".ready"}, ctx)
    page.wait_for_selector.assert_awaited_once_with(".ready", timeout=10000)
    assert ".ready" in result.content[0]["text"]


async def test_back(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "back"}, ctx)
    page.go_back.assert_awaited_once()


async def test_forward(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "forward"}, ctx)
    page.go_forward.assert_awaited_once()


async def test_unknown_action_returns_error(ctx):
    page = _mock_page()
    with _patch_browser(page):
        result = await _call({"action": "teleport"}, ctx)
    assert result.is_error
    assert "Unknown action" in result.content[0]["text"]


async def test_exception_returns_error(ctx):
    page = _mock_page()
    page.goto = AsyncMock(side_effect=Exception("net error"))
    with _patch_browser(page):
        result = await _call({"action": "open", "url": "bad"}, ctx)
    assert result.is_error
    assert "Browser error" in result.content[0]["text"]
