from src.context import ToolUseContext
from src.tool import Tool, ToolResult, build_tool
from src.tools.tool_search_tool import _call


def _make_tool(name, description, search_hint=""):
    async def _c(args, ctx):
        return ToolResult(content=[{"type": "text", "text": "ok"}])

    return build_tool(
        Tool(
            name=name,
            description=description,
            input_schema={"type": "object", "properties": {}, "required": []},
            call=_c,
            search_hint=search_hint,
        )
    )


def _ctx_with_tools(*tools):
    return ToolUseContext(
        model="claude-sonnet-4-6",
        messages=[],
        tools=list(tools),
    )


async def test_keyword_match(ctx):
    t1 = _make_tool("FileRead", "Read a file", "file read open")
    t2 = _make_tool("FileWrite", "Write a file", "file write save")
    c = _ctx_with_tools(t1, t2)
    result = await _call({"query": "file"}, c)
    text = result.content[0]["text"]
    assert "FileRead" in text
    assert "FileWrite" in text


async def test_select_by_name(ctx):
    t1 = _make_tool("Alpha", "desc", "hint")
    t2 = _make_tool("Beta", "desc", "hint")
    c = _ctx_with_tools(t1, t2)
    result = await _call({"query": "select:Alpha"}, c)
    text = result.content[0]["text"]
    assert "Alpha" in text
    assert "Beta" not in text


async def test_no_match_returns_message(ctx):
    c = _ctx_with_tools(_make_tool("Only", "desc", "hint"))
    result = await _call({"query": "xyzzy"}, c)
    assert "No matching tools found" in result.content[0]["text"]


async def test_max_results_respected(ctx):
    tools = [_make_tool(f"T{i}", "file tool", "file") for i in range(10)]
    c = _ctx_with_tools(*tools)
    result = await _call({"query": "file", "max_results": 3}, c)
    lines = [l for l in result.content[0]["text"].split("\n") if l.strip()]
    assert len(lines) == 3


async def test_select_multiple(ctx):
    t1 = _make_tool("Alpha", "d", "")
    t2 = _make_tool("Beta", "d", "")
    t3 = _make_tool("Gamma", "d", "")
    c = _ctx_with_tools(t1, t2, t3)
    result = await _call({"query": "select:Alpha,Gamma"}, c)
    text = result.content[0]["text"]
    assert "Alpha" in text
    assert "Gamma" in text
    assert "Beta" not in text
