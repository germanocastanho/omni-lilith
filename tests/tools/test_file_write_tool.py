import pytest

from src.tools.file_write_tool import _call


async def test_write_creates_file(ctx, tmp_path):
    f = tmp_path / "out.txt"
    result = await _call({"file_path": str(f), "content": "hello"}, ctx)
    assert not result.is_error
    assert f.read_text() == "hello"


async def test_write_overwrites_existing(ctx, tmp_path):
    f = tmp_path / "out.txt"
    f.write_text("old content")
    await _call({"file_path": str(f), "content": "new content"}, ctx)
    assert f.read_text() == "new content"


async def test_write_creates_parent_dirs(ctx, tmp_path):
    f = tmp_path / "a" / "b" / "c.txt"
    result = await _call({"file_path": str(f), "content": "deep"}, ctx)
    assert not result.is_error
    assert f.exists()


async def test_write_returns_path_in_message(ctx, tmp_path):
    f = tmp_path / "x.txt"
    result = await _call({"file_path": str(f), "content": ""}, ctx)
    assert str(f) in result.content[0]["text"]


async def test_write_empty_content(ctx, tmp_path):
    f = tmp_path / "empty.txt"
    await _call({"file_path": str(f), "content": ""}, ctx)
    assert f.read_text() == ""
