from src.tools.synthetic_output_tool import _call


async def test_injects_user_message_by_default(ctx):
    initial_len = len(ctx.messages)
    result = await _call({"content": "injected content"}, ctx)
    assert not result.is_error
    assert len(ctx.messages) == initial_len + 1
    msg = ctx.messages[-1]
    assert msg["role"] == "user"
    assert msg["content"] == "injected content"


async def test_injects_assistant_message(ctx):
    initial_len = len(ctx.messages)
    result = await _call({"content": "my response", "role": "assistant"}, ctx)
    assert not result.is_error
    assert ctx.messages[-1]["role"] == "assistant"
    assert ctx.messages[-1]["content"] == "my response"


async def test_result_text_mentions_role(ctx):
    result = await _call({"content": "x", "role": "user"}, ctx)
    assert "user" in result.content[0]["text"]
