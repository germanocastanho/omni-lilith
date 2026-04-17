import json

import pytest

from src.tools.notebook_edit_tool import _call


def _make_notebook(tmp_path, cells=None):
    if cells is None:
        cells = [
            {"cell_type": "code", "source": "x = 1", "metadata": {}, "outputs": []},
            {"cell_type": "markdown", "source": "# Title", "metadata": {}},
        ]
    nb = {"nbformat": 4, "nbformat_minor": 5, "metadata": {}, "cells": cells}
    path = tmp_path / "test.ipynb"
    path.write_text(json.dumps(nb), encoding="utf-8")
    return path


async def test_nonexistent_notebook_returns_error(ctx, tmp_path):
    result = await _call({"notebook_path": str(tmp_path / "missing.ipynb")}, ctx)
    assert result.is_error
    assert "not found" in result.content[0]["text"]


async def test_list_cells(ctx, tmp_path):
    path = _make_notebook(tmp_path)
    result = await _call({"notebook_path": str(path)}, ctx)
    assert not result.is_error
    text = result.content[0]["text"]
    assert "[0]" in text
    assert "[1]" in text
    assert "code" in text
    assert "markdown" in text


async def test_empty_notebook(ctx, tmp_path):
    path = _make_notebook(tmp_path, cells=[])
    result = await _call({"notebook_path": str(path)}, ctx)
    assert "(empty notebook)" in result.content[0]["text"]


async def test_edit_cell_source(ctx, tmp_path):
    path = _make_notebook(tmp_path)
    result = await _call(
        {"notebook_path": str(path), "cell_index": 0, "new_source": "y = 2"}, ctx
    )
    assert not result.is_error
    assert "Cell 0 updated" in result.content[0]["text"]
    nb = json.loads(path.read_text())
    assert nb["cells"][0]["source"] == "y = 2"


async def test_edit_cell_index_out_of_range(ctx, tmp_path):
    path = _make_notebook(tmp_path)
    result = await _call(
        {"notebook_path": str(path), "cell_index": 99, "new_source": "oops"}, ctx
    )
    assert result.is_error
    assert "out of range" in result.content[0]["text"]


async def test_insert_cell_after(ctx, tmp_path):
    path = _make_notebook(tmp_path)
    result = await _call(
        {
            "notebook_path": str(path),
            "insert_after": 0,
            "cell_type": "code",
            "new_source": "z = 3",
        },
        ctx,
    )
    assert not result.is_error
    assert "Inserted" in result.content[0]["text"]
    nb = json.loads(path.read_text())
    assert nb["cells"][1]["source"] == "z = 3"
    assert nb["cells"][1]["cell_type"] == "code"


async def test_insert_markdown_cell(ctx, tmp_path):
    path = _make_notebook(tmp_path)
    result = await _call(
        {
            "notebook_path": str(path),
            "insert_after": -1,
            "cell_type": "markdown",
            "new_source": "## New section",
        },
        ctx,
    )
    assert not result.is_error
    nb = json.loads(path.read_text())
    last = nb["cells"][-1]
    assert last["cell_type"] == "markdown"
    assert last["source"] == "## New section"
