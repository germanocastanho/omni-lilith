from src.tools.lsp_tool import _call


async def test_always_returns_error(ctx):
    result = await _call({"method": "textDocument/definition"}, ctx)
    assert result.is_error
    assert "not yet configured" in result.content[0]["text"]


async def test_with_params_still_error(ctx):
    result = await _call(
        {"method": "textDocument/hover", "params": {"line": 1}, "language_id": "python"},
        ctx,
    )
    assert result.is_error
