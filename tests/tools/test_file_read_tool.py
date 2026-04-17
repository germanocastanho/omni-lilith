import pytest

from src.tools.file_read_tool import _call


async def test_read_full_file(ctx, tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("line1\nline2\nline3\n")
    result = await _call({"file_path": str(f)}, ctx)
    text = result.content[0]["text"]
    assert "1\tline1" in text
    assert "2\tline2" in text
    assert "3\tline3" in text
    assert not result.is_error


async def test_read_with_offset(ctx, tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("a\nb\nc\n")
    result = await _call({"file_path": str(f), "offset": 2}, ctx)
    text = result.content[0]["text"]
    assert "1\t" not in text
    assert "2\tb" in text
    assert "3\tc" in text


async def test_read_with_limit(ctx, tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("a\nb\nc\nd\n")
    result = await _call({"file_path": str(f), "limit": 2}, ctx)
    text = result.content[0]["text"]
    assert "1\ta" in text
    assert "2\tb" in text
    assert "c" not in text


async def test_read_offset_and_limit(ctx, tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("a\nb\nc\nd\n")
    result = await _call({"file_path": str(f), "offset": 2, "limit": 2}, ctx)
    text = result.content[0]["text"]
    assert "2\tb" in text
    assert "3\tc" in text
    assert "d" not in text


async def test_read_missing_file(ctx, tmp_path):
    result = await _call({"file_path": str(tmp_path / "nope.txt")}, ctx)
    assert result.is_error
    assert "not found" in result.content[0]["text"]
