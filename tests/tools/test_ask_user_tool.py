from unittest.mock import patch

from src.tools.ask_user_tool import _call


def _patch_prompt(answer):
    return patch("rich.prompt.Prompt.ask", return_value=answer)


async def test_free_text_question(ctx):
    with _patch_prompt("my answer"):
        result = await _call({"question": "What is your name?"}, ctx)
    assert result.content[0]["text"] == "my answer"
    assert not result.is_error


async def test_with_options_returns_chosen_option(ctx):
    with _patch_prompt("2"):
        result = await _call(
            {"question": "Pick one", "options": ["alpha", "beta", "gamma"]}, ctx
        )
    assert result.content[0]["text"] == "beta"


async def test_with_options_first_choice(ctx):
    with _patch_prompt("1"):
        result = await _call(
            {"question": "Pick", "options": ["yes", "no"]}, ctx
        )
    assert result.content[0]["text"] == "yes"
