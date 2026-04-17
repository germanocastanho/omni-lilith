from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

import src.tools.skill_tool as skill_mod
from src.tools.skill_tool import _call


def _patch_skills_dir(path: Path):
    return patch.object(skill_mod, "_SKILLS_DIR", path)


def _patch_run_query(return_value="skill result"):
    return patch("src.query_engine.run_query", new=AsyncMock(return_value=return_value))


async def test_list_skills_no_dir(ctx, tmp_path):
    ghost = tmp_path / "no_skills"
    with _patch_skills_dir(ghost):
        result = await _call({}, ctx)
    assert "No skills directory found" in result.content[0]["text"]
    assert not result.is_error


async def test_list_skills_empty_dir(ctx, tmp_path):
    with _patch_skills_dir(tmp_path):
        result = await _call({}, ctx)
    assert "No skills available" in result.content[0]["text"]


async def test_list_skills_shows_names(ctx, tmp_path):
    for name in ["alpha", "beta"]:
        skill_dir = tmp_path / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# skill")
    with _patch_skills_dir(tmp_path):
        result = await _call({}, ctx)
    text = result.content[0]["text"]
    assert "alpha" in text
    assert "beta" in text


async def test_list_ignores_dirs_without_skill_md(ctx, tmp_path):
    (tmp_path / "no_md").mkdir()
    skill_dir = tmp_path / "valid"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# skill")
    with _patch_skills_dir(tmp_path):
        result = await _call({}, ctx)
    assert "valid" in result.content[0]["text"]
    assert "no_md" not in result.content[0]["text"]


async def test_skill_not_found(ctx, tmp_path):
    with _patch_skills_dir(tmp_path):
        result = await _call({"skill": "ghost"}, ctx)
    assert result.is_error
    assert "ghost" in result.content[0]["text"]


async def test_skill_executes_and_returns_result(ctx, tmp_path):
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("Do the thing.")
    with _patch_skills_dir(tmp_path), _patch_run_query("done!"):
        result = await _call({"skill": "my_skill"}, ctx)
    assert result.content[0]["text"] == "done!"
    assert not result.is_error


async def test_skill_appends_args_to_prompt(ctx, tmp_path):
    skill_dir = tmp_path / "sk"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("Base prompt.")
    with _patch_skills_dir(tmp_path), _patch_run_query() as mock:
        await _call({"skill": "sk", "args": "extra arg"}, ctx)
    call_ctx = mock.call_args[0][0]
    user_msg = call_ctx.messages[0]["content"]
    assert "Base prompt." in user_msg
    assert "extra arg" in user_msg


async def test_skill_no_output_fallback(ctx, tmp_path):
    skill_dir = tmp_path / "sk"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("prompt")
    with _patch_skills_dir(tmp_path), _patch_run_query(None):
        result = await _call({"skill": "sk"}, ctx)
    assert result.content[0]["text"] == "(no output)"
