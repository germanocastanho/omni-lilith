import pytest

import src.tools.task_tools as task_mod
from src.tools.task_tools import (
    _create,
    _get,
    _list,
    _output,
    _stop,
    _update,
)


@pytest.fixture(autouse=True)
def clear_tasks():
    task_mod._tasks.clear()
    yield
    task_mod._tasks.clear()


async def test_create_task(ctx):
    result = await _create({"subject": "Fix bug", "description": "Details"}, ctx)
    assert not result.is_error
    assert "Fix bug" in result.content[0]["text"]
    assert len(task_mod._tasks) == 1


async def test_list_empty(ctx):
    result = await _list({}, ctx)
    assert "No tasks" in result.content[0]["text"]


async def test_list_shows_tasks(ctx):
    await _create({"subject": "A", "description": "x"}, ctx)
    await _create({"subject": "B", "description": "y"}, ctx)
    result = await _list({}, ctx)
    text = result.content[0]["text"]
    assert "A" in text
    assert "B" in text


async def test_get_task(ctx):
    await _create({"subject": "My task", "description": "desc"}, ctx)
    task_id = list(task_mod._tasks.keys())[0]
    result = await _get({"taskId": task_id}, ctx)
    assert not result.is_error
    assert "My task" in result.content[0]["text"]


async def test_get_nonexistent_returns_error(ctx):
    result = await _get({"taskId": "nope"}, ctx)
    assert result.is_error
    assert "not found" in result.content[0]["text"]


async def test_update_status(ctx):
    await _create({"subject": "T", "description": "d"}, ctx)
    task_id = list(task_mod._tasks.keys())[0]
    result = await _update({"taskId": task_id, "status": "in_progress"}, ctx)
    assert not result.is_error
    assert task_mod._tasks[task_id].status == "in_progress"


async def test_update_deletes_task(ctx):
    await _create({"subject": "T", "description": "d"}, ctx)
    task_id = list(task_mod._tasks.keys())[0]
    result = await _update({"taskId": task_id, "status": "deleted"}, ctx)
    assert not result.is_error
    assert task_id not in task_mod._tasks


async def test_update_nonexistent_returns_error(ctx):
    result = await _update({"taskId": "ghost", "status": "completed"}, ctx)
    assert result.is_error


async def test_stop_task(ctx):
    await _create({"subject": "T", "description": "d"}, ctx)
    task_id = list(task_mod._tasks.keys())[0]
    result = await _stop({"taskId": task_id}, ctx)
    assert not result.is_error
    assert task_mod._tasks[task_id].status == "stopped"


async def test_stop_nonexistent_returns_error(ctx):
    result = await _stop({"taskId": "ghost"}, ctx)
    assert result.is_error


async def test_output_empty(ctx):
    await _create({"subject": "T", "description": "d"}, ctx)
    task_id = list(task_mod._tasks.keys())[0]
    result = await _output({"taskId": task_id}, ctx)
    assert "(no output yet)" in result.content[0]["text"]


async def test_output_with_lines(ctx):
    await _create({"subject": "T", "description": "d"}, ctx)
    task_id = list(task_mod._tasks.keys())[0]
    task_mod._tasks[task_id].output = ["line1", "line2", "line3"]
    result = await _output({"taskId": task_id, "lines": 2}, ctx)
    text = result.content[0]["text"]
    assert "line2" in text
    assert "line3" in text
    assert "line1" not in text


async def test_output_nonexistent_returns_error(ctx):
    result = await _output({"taskId": "ghost"}, ctx)
    assert result.is_error
