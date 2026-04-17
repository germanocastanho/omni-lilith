import json

import src.tools.todo_write_tool as todo_mod
from src.tools.todo_write_tool import _call


def _patch_todos_path(tmp_path):
    from unittest.mock import patch
    return patch.object(todo_mod, "_TODOS_PATH", tmp_path / "todos.json")


async def test_saves_todos_to_file(ctx, tmp_path):
    todos = [
        {"id": "1", "content": "Buy milk", "status": "pending", "priority": "low"},
    ]
    with _patch_todos_path(tmp_path):
        result = await _call({"todos": todos}, ctx)
    assert not result.is_error
    saved = json.loads((tmp_path / "todos.json").read_text())
    assert saved[0]["content"] == "Buy milk"


async def test_status_counts_in_response(ctx, tmp_path):
    todos = [
        {"id": "1", "content": "A", "status": "pending", "priority": "high"},
        {"id": "2", "content": "B", "status": "in_progress", "priority": "medium"},
        {"id": "3", "content": "C", "status": "completed", "priority": "low"},
        {"id": "4", "content": "D", "status": "completed", "priority": "low"},
    ]
    with _patch_todos_path(tmp_path):
        result = await _call({"todos": todos}, ctx)
    text = result.content[0]["text"]
    assert "4 total" in text
    assert "1 pending" in text
    assert "1 in_progress" in text
    assert "2 done" in text


async def test_empty_todos_list(ctx, tmp_path):
    with _patch_todos_path(tmp_path):
        result = await _call({"todos": []}, ctx)
    assert not result.is_error
    assert "0 total" in result.content[0]["text"]
