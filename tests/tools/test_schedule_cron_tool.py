from unittest.mock import patch

import src.tools.schedule_cron_tool as cron_mod
from src.tools.schedule_cron_tool import _create, _delete, _list


def _patch_storage(crons=None):
    crons = list(crons) if crons else []
    saved = []

    def _load():
        return list(crons)

    def _save(data):
        crons.clear()
        crons.extend(data)
        saved.extend(data)

    return patch.object(cron_mod, "_load", _load), patch.object(cron_mod, "_save", _save), crons


async def test_create_new_cron(ctx):
    load_p, save_p, _ = _patch_storage()
    with load_p, save_p:
        result = await _create(
            {"name": "daily", "schedule": "0 9 * * *", "prompt": "Good morning"}, ctx
        )
    assert not result.is_error
    assert "daily" in result.content[0]["text"]


async def test_create_duplicate_returns_error(ctx):
    existing = [{"name": "daily", "schedule": "0 9 * * *", "prompt": "x"}]
    load_p, save_p, _ = _patch_storage(existing)
    with load_p, save_p:
        result = await _create(
            {"name": "daily", "schedule": "0 9 * * *", "prompt": "y"}, ctx
        )
    assert result.is_error
    assert "already exists" in result.content[0]["text"]


async def test_delete_existing_cron(ctx):
    existing = [{"name": "daily", "schedule": "0 9 * * *", "prompt": "x"}]
    load_p, save_p, crons = _patch_storage(existing)
    with load_p, save_p:
        result = await _delete({"name": "daily"}, ctx)
    assert not result.is_error
    assert "deleted" in result.content[0]["text"]


async def test_delete_nonexistent_returns_error(ctx):
    load_p, save_p, _ = _patch_storage()
    with load_p, save_p:
        result = await _delete({"name": "ghost"}, ctx)
    assert result.is_error
    assert "not found" in result.content[0]["text"]


async def test_list_empty(ctx):
    load_p, save_p, _ = _patch_storage()
    with load_p, save_p:
        result = await _list({}, ctx)
    assert "No crons" in result.content[0]["text"]


async def test_list_shows_crons(ctx):
    existing = [
        {"name": "morning", "schedule": "0 9 * * *", "prompt": "Hello"},
        {"name": "night", "schedule": "0 22 * * *", "prompt": "Goodnight"},
    ]
    load_p, save_p, _ = _patch_storage(existing)
    with load_p, save_p:
        result = await _list({}, ctx)
    text = result.content[0]["text"]
    assert "morning" in text
    assert "night" in text
