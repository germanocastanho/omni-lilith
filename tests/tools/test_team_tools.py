from unittest.mock import patch

import src.tools.team_tools as team_mod
from src.tools.team_tools import _create, _delete


def _patch_storage(teams=None):
    teams = list(teams) if teams else []

    def _load():
        return list(teams)

    def _save(data):
        teams.clear()
        teams.extend(data)

    return patch.object(team_mod, "_load", _load), patch.object(team_mod, "_save", _save)


async def test_create_team(ctx):
    load_p, save_p = _patch_storage()
    with load_p, save_p:
        result = await _create(
            {"name": "alpha", "agents": ["researcher", "coder"], "description": "dev team"},
            ctx,
        )
    assert not result.is_error
    assert "alpha" in result.content[0]["text"]
    assert "2" in result.content[0]["text"]


async def test_create_duplicate_returns_error(ctx):
    existing = [{"name": "alpha", "agents": [], "description": ""}]
    load_p, save_p = _patch_storage(existing)
    with load_p, save_p:
        result = await _create({"name": "alpha", "agents": []}, ctx)
    assert result.is_error
    assert "already exists" in result.content[0]["text"]


async def test_delete_team(ctx):
    existing = [{"name": "alpha", "agents": [], "description": ""}]
    load_p, save_p = _patch_storage(existing)
    with load_p, save_p:
        result = await _delete({"name": "alpha"}, ctx)
    assert not result.is_error
    assert "deleted" in result.content[0]["text"]


async def test_delete_nonexistent_returns_error(ctx):
    load_p, save_p = _patch_storage()
    with load_p, save_p:
        result = await _delete({"name": "ghost"}, ctx)
    assert result.is_error
    assert "not found" in result.content[0]["text"]
