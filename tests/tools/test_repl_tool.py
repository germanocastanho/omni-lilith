import src.tools.repl_tool as repl_mod
from src.tools.repl_tool import _call


async def _run(code, ctx):
    repl_mod._repl_namespace.clear()
    return await _call({"code": code}, ctx)


async def test_basic_output(ctx):
    result = await _run("print('hello')", ctx)
    assert result.content[0]["text"] == "hello\n"
    assert not result.is_error


async def test_no_output_fallback(ctx):
    result = await _run("x = 1", ctx)
    assert result.content[0]["text"] == "(no output)"


async def test_error_in_stderr(ctx):
    result = await _run("raise ValueError('oops')", ctx)
    assert "<stderr>" in result.content[0]["text"]
    assert "oops" in result.content[0]["text"]


async def test_namespace_persists_across_calls(ctx):
    await _call({"code": "counter = 10"}, ctx)
    result = await _call({"code": "print(counter)"}, ctx)
    assert "10" in result.content[0]["text"]


async def test_multiple_prints(ctx):
    result = await _run("print(1)\nprint(2)", ctx)
    assert "1" in result.content[0]["text"]
    assert "2" in result.content[0]["text"]
