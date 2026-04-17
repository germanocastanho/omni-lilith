from src.tools.mcp_resource_tools import _list, _read


async def test_list_not_implemented(ctx):
    result = await _list({"server_name": "s"}, ctx)
    assert not result.is_error
    assert "not yet implemented" in result.content[0]["text"]


async def test_read_not_implemented(ctx):
    result = await _read({"server_name": "s", "uri": "mem://foo"}, ctx)
    assert not result.is_error
    assert "not yet implemented" in result.content[0]["text"]
