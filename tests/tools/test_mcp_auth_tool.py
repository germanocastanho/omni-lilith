from src.tools.mcp_auth_tool import _call


async def test_always_returns_error(ctx):
    result = await _call({"server_name": "my_server"}, ctx)
    assert result.is_error
    assert "not yet configured" in result.content[0]["text"]


async def test_with_token_still_error(ctx):
    result = await _call({"server_name": "x", "token": "abc123"}, ctx)
    assert result.is_error
