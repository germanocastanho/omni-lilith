from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.context import ToolUseContext
from src.query_engine import (
    _dispatch_tools,
    _find_tool,
    _summarize_args,
    _tool_error,
)
from src.tool import PermissionResult, Tool, ToolResult, build_tool


# --- helpers ---

def _make_tool(name="Echo"):
    async def _call(args, ctx):
        return ToolResult(content=[{"type": "text", "text": args.get("text", "ok")}])

    return build_tool(Tool(
        name=name,
        description="echo",
        input_schema={"type": "object", "properties": {}, "required": []},
        call=_call,
    ))


def _ctx(*tools):
    return ToolUseContext(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "hi"}],
        tools=list(tools),
    )


def _allow(args=None):
    return PermissionResult(behavior="allow", updated_input=args or {})


def _deny(msg="denied"):
    return PermissionResult(behavior="deny", message=msg)


# --- events (names must match type(event).__name__ checks in run_query) ---

class RawContentBlockStartEvent:
    def __init__(self, block):
        self.content_block = block


class RawContentBlockDeltaEvent:
    def __init__(self, delta):
        self.delta = delta


class RawContentBlockStopEvent:
    pass


class RawMessageDeltaEvent:
    def __init__(self, stop_reason):
        self.delta = SimpleNamespace(stop_reason=stop_reason)


def _text_block():
    return SimpleNamespace(type="text")


def _tool_block(tool_id="t1", name="Echo"):
    return SimpleNamespace(type="tool_use", id=tool_id, name=name)


def _text_delta(text):
    return SimpleNamespace(type="text_delta", text=text)


def _json_delta(partial):
    return SimpleNamespace(type="input_json_delta", partial_json=partial)


async def _stream(*events):
    for e in events:
        yield e


def _patch_stream(events):
    return patch(
        "src.services.api.stream_query",
        return_value=_stream(*events),
    )


def _patch_live():
    live = MagicMock()
    live.__enter__ = MagicMock(return_value=live)
    live.__exit__ = MagicMock(return_value=False)
    live.update = MagicMock()
    return patch("src.query_engine.Live", return_value=live)


def _patch_perm(result=None):
    result = result or _allow()
    return patch(
        "src.query_engine.check_tool_permission",
        new=AsyncMock(return_value=result),
    )


# --- _find_tool ---

def test_find_tool_by_name():
    t = _make_tool("Alpha")
    assert _find_tool([t], "Alpha") is t


def test_find_tool_not_found():
    assert _find_tool([_make_tool("Alpha")], "Beta") is None


def test_find_tool_empty_list():
    assert _find_tool([], "X") is None


# --- _tool_error ---

def test_tool_error_structure():
    err = _tool_error("id-1", "bad thing")
    assert err["type"] == "tool_result"
    assert err["tool_use_id"] == "id-1"
    assert err["is_error"] is True
    assert "bad thing" in err["content"][0]["text"]


# --- _summarize_args ---

def test_summarize_args_short():
    assert _summarize_args({"a": 1}) == '{"a": 1}'


def test_summarize_args_truncated():
    long_args = {"key": "x" * 200}
    result = _summarize_args(long_args)
    assert result.endswith("...")
    assert len(result) <= 83


# --- _dispatch_tools ---

async def test_dispatch_unknown_tool():
    ctx = _ctx()
    results = await _dispatch_tools(
        [{"id": "x", "name": "Ghost", "input": {}}], ctx
    )
    assert results[0]["is_error"] is True
    assert "Unknown tool" in results[0]["content"][0]["text"]


async def test_dispatch_permission_denied():
    tool = _make_tool("Echo")
    ctx = _ctx(tool)
    with _patch_perm(_deny("not allowed")):
        results = await _dispatch_tools(
            [{"id": "x", "name": "Echo", "input": {}}], ctx
        )
    assert results[0]["is_error"] is True
    assert "Permission denied" in results[0]["content"][0]["text"]


async def test_dispatch_successful_call():
    tool = _make_tool("Echo")
    ctx = _ctx(tool)
    with _patch_perm(_allow({"text": "hello"})):
        results = await _dispatch_tools(
            [{"id": "x", "name": "Echo", "input": {"text": "hello"}}], ctx
        )
    assert not results[0]["is_error"]
    assert results[0]["content"][0]["text"] == "hello"


async def test_dispatch_tool_exception_returns_error():
    async def _boom(args, ctx):
        raise RuntimeError("exploded")

    tool = build_tool(Tool(
        name="Boom",
        description="boom",
        input_schema={"type": "object", "properties": {}, "required": []},
        call=_boom,
    ))
    ctx = _ctx(tool)
    with _patch_perm(_allow({})):
        results = await _dispatch_tools(
            [{"id": "x", "name": "Boom", "input": {}}], ctx
        )
    assert results[0]["is_error"] is True
    assert "exploded" in results[0]["content"][0]["text"]


async def test_dispatch_multiple_tools():
    t1 = _make_tool("T1")
    t2 = _make_tool("T2")
    ctx = _ctx(t1, t2)
    with _patch_perm(_allow({})):
        results = await _dispatch_tools(
            [
                {"id": "a", "name": "T1", "input": {}},
                {"id": "b", "name": "T2", "input": {}},
            ],
            ctx,
        )
    assert len(results) == 2
    assert results[0]["tool_use_id"] == "a"
    assert results[1]["tool_use_id"] == "b"


# --- run_query ---

async def test_run_query_simple_text_response():
    from src.query_engine import run_query

    events = [
        RawContentBlockStartEvent(_text_block()),
        RawContentBlockDeltaEvent(_text_delta("Hello")),
        RawContentBlockDeltaEvent(_text_delta(", world")),
        RawContentBlockStopEvent(),
        RawMessageDeltaEvent("end_turn"),
    ]
    ctx = _ctx()
    with _patch_stream(events), _patch_live():
        result = await run_query(ctx)

    assert result == "Hello, world"
    assert ctx.messages[-1] == {"role": "assistant", "content": "Hello, world"}


async def test_run_query_empty_stream_returns_empty():
    from src.query_engine import run_query

    events = [RawMessageDeltaEvent("end_turn")]
    ctx = _ctx()
    with _patch_stream(events), _patch_live():
        result = await run_query(ctx)

    assert result == ""


async def test_run_query_tool_use_then_end():
    from src.query_engine import run_query

    tool = _make_tool("Echo")

    first_turn = [
        RawContentBlockStartEvent(_tool_block("tid", "Echo")),
        RawContentBlockDeltaEvent(_json_delta('{"text"')),
        RawContentBlockDeltaEvent(_json_delta(': "hi"}')),
        RawContentBlockStopEvent(),
        RawMessageDeltaEvent("tool_use"),
    ]
    second_turn = [
        RawContentBlockStartEvent(_text_block()),
        RawContentBlockDeltaEvent(_text_delta("done")),
        RawContentBlockStopEvent(),
        RawMessageDeltaEvent("end_turn"),
    ]

    call_count = 0

    async def _fake_stream(ctx):
        nonlocal call_count
        call_count += 1
        events = first_turn if call_count == 1 else second_turn
        for e in events:
            yield e

    ctx = _ctx(tool)
    with patch("src.services.api.stream_query", side_effect=_fake_stream), \
         _patch_live(), \
         _patch_perm(_allow({"text": "hi"})):
        result = await run_query(ctx)

    assert result == "done"
    assert call_count == 2


async def test_run_query_aborted_breaks_immediately():
    from src.query_engine import run_query

    ctx = _ctx()
    ctx.abort_event.set()

    events = [RawContentBlockStartEvent(_text_block()), RawContentBlockDeltaEvent(_text_delta("never"))]
    with _patch_stream(events), _patch_live():
        result = await run_query(ctx)

    assert result == ""


async def test_run_query_invalid_json_input_defaults_to_empty():
    from src.query_engine import run_query

    tool = _make_tool("Echo")

    first_turn = [
        RawContentBlockStartEvent(_tool_block("tid", "Echo")),
        RawContentBlockDeltaEvent(_json_delta("NOT_JSON")),
        RawContentBlockStopEvent(),
        RawMessageDeltaEvent("tool_use"),
    ]
    second_turn = [
        RawContentBlockStartEvent(_text_block()),
        RawContentBlockDeltaEvent(_text_delta("ok")),
        RawContentBlockStopEvent(),
        RawMessageDeltaEvent("end_turn"),
    ]

    call_count = 0

    async def _fake_stream(ctx):
        nonlocal call_count
        call_count += 1
        events = first_turn if call_count == 1 else second_turn
        for e in events:
            yield e

    ctx = _ctx(tool)
    with patch("src.services.api.stream_query", side_effect=_fake_stream), \
         _patch_live(), \
         _patch_perm(_allow({})):
        result = await run_query(ctx)

    assert result == "ok"
