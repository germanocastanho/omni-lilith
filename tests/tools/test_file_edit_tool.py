import pytest

from src.tools.file_edit_tool import _call


async def test_edit_replaces_unique_string(ctx, tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("hello world")
    result = await _call(
        {"file_path": str(f), "old_string": "world", "new_string": "Lilith"},
        ctx,
    )
    assert not result.is_error
    assert f.read_text() == "hello Lilith"


async def test_edit_missing_file(ctx, tmp_path):
    result = await _call(
        {"file_path": str(tmp_path / "nope.txt"), "old_string": "x", "new_string": "y"},
        ctx,
    )
    assert result.is_error
    assert "not found" in result.content[0]["text"]


async def test_edit_old_string_not_found(ctx, tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("hello")
    result = await _call(
        {"file_path": str(f), "old_string": "NOPE", "new_string": "x"},
        ctx,
    )
    assert result.is_error
    assert "not found" in result.content[0]["text"]


async def test_edit_duplicate_without_replace_all_errors(ctx, tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("foo foo foo")
    result = await _call(
        {"file_path": str(f), "old_string": "foo", "new_string": "bar"},
        ctx,
    )
    assert result.is_error
    assert "3 times" in result.content[0]["text"]


async def test_edit_replace_all(ctx, tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("foo foo foo")
    result = await _call(
        {"file_path": str(f), "old_string": "foo", "new_string": "bar", "replace_all": True},
        ctx,
    )
    assert not result.is_error
    assert f.read_text() == "bar bar bar"


async def test_edit_reports_replacement_count(ctx, tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("x x x")
    result = await _call(
        {"file_path": str(f), "old_string": "x", "new_string": "y", "replace_all": True},
        ctx,
    )
    assert "3" in result.content[0]["text"]
